#!/usr/bin/python
# -*- coding: UTF-8 -*-
# crawler for http://schools.nyc.gov/schoolsearch/Maps.aspx
import requests
import json
import re

HEADERS = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1581.2 Safari/537.36',
    'Content-Type':'application/json',
}

ESRI_GEOMETRY_POINT_URL = 'http://maps.nycboe.net/ArcGIS/rest/services/Geometry/GeometryServer/project'
XY_POINT_URL = 'http://schools.nyc.gov/schoolsearch/services/SchoolRpc.ashx?rpc'
RINGS_URL = 'http://maps.nycboe.net/ArcGIS/rest/services/Geometry/GeometryServer/buffer'
ZONED_LOC_CODE_URL = 'http://maps.nycboe.net/ArcGIS/rest/services/SchoolSearch/CnFZones/MapServer/identify'
ZONED_SCHOOL_URL = 'http://schools.nyc.gov/schoolsearch/services/SchoolRpc.ashx?rpc'

def get_xy_point(address):
    xy_point_payload = {
        'id': 0,
        'method': 'findAddress',
        'params': {
            'mode': 'findaddress',
            'action': 'findaddress',
            'address': address,
            'borough': ''
        },
        'jsonrpc': '2.0'
    }
    xy_point_result = requests.post(XY_POINT_URL, headers=HEADERS, json=xy_point_payload).json()
    if len(xy_point_result['result']['results']) == 0:
        return None
    xy_point = {
        'x': int(xy_point_result['result']['results'][0]['x']),
        'y': int(xy_point_result['result']['results'][0]['y'])
    }
    return xy_point

def get_esri_geometries_point(xy_point):
    geometries_string_for_esri_geometry_point = '{{"geometryType":"esriGeometryPoint","geometries":[{{"x":{},"y":{},"spatialReference":{{"wkid":2263}}}}]}}'.format(xy_point['x'], xy_point['y'])
    esri_geometry_point_payload = {
        'f': 'json',
        'outSR': '3857',
        'inSR': '2263',
        'geometries': geometries_string_for_esri_geometry_point,
        'callback': 'dojo.io.script.jsonp_dojoIoScript9._jsonpCallback'
    }
    esri_geometry_point_result = requests.get(ESRI_GEOMETRY_POINT_URL, headers=HEADERS, params=esri_geometry_point_payload)
    esri_geometry_point_result = esri_geometry_point_result.text.replace('dojo.io.script.jsonp_dojoIoScript9._jsonpCallback(', '')
    esri_geometry_point_result = esri_geometry_point_result.replace(');', '')
    esri_geometry_point_result = json.loads(esri_geometry_point_result)
    esri_geometry_point = esri_geometry_point_result['geometries'][0]
    return esri_geometry_point

def get_zoned_loc_code_list(esri_geometry_point):
    geometries_string_for_zoned_loc_code = '{{"x":{},"y":{},"spatialReference":{{"wkid":102100}}}}'.format(esri_geometry_point['x'], esri_geometry_point['y'])
    zoned_loc_code_payload = {
        'f': 'json',
        'geometry': geometries_string_for_zoned_loc_code,
        'tolerance': 0,
        'returnGeometry': False,
        'mapExtent': '{"xmin":-8310019.783945783,"ymin":4910796.362276962,"xmax":-8158980.216054217,"ymax":5028203.637723038,"spatialReference":{"wkid":102100}}',
        'imageDisplay': '988,768,96',
        'geometryType': 'esriGeometryPoint',
        'sr': 102100,
        'layers': 'all:0,1',
        'callback': 'dojo.io.script.jsonp_dojoIoScript11._jsonpCallback'
    }
    zoned_loc_code_result = requests.get(ZONED_LOC_CODE_URL, headers=HEADERS, params=zoned_loc_code_payload)
    zoned_loc_code_result = zoned_loc_code_result.text.replace('dojo.io.script.jsonp_dojoIoScript11._jsonpCallback(', '')
    zoned_loc_code_result = zoned_loc_code_result.replace(');', '')
    zoned_loc_code_result = json.loads(zoned_loc_code_result)
    zoned_loc_code_list = []
    es_dbn = zoned_loc_code_result['results'][0]['attributes']['ESDBN'].split(',')
    es_notes = zoned_loc_code_result['results'][0]['attributes']['ESNotes']
    if len(es_dbn) != 0:
        for es in es_dbn:
            if es != '':
                index = re.search('[a-zA-Z]', es)
                zoned_loc_code_list.append(es[index.start():])
    ms_dbn = zoned_loc_code_result['results'][0]['attributes']['MSDBN'].split(',')
    ms_notes = zoned_loc_code_result['results'][0]['attributes']['MSNotes']
    if len(ms_dbn) != 0:
        for ms in ms_dbn:
            if ms != '':
                index = re.search('[a-zA-Z]', ms)
                zoned_loc_code_list.append(ms[index.start():])
    hs_dbn = zoned_loc_code_result['results'][0]['attributes']['HSDBN'].split(',')
    hs_notes = zoned_loc_code_result['results'][0]['attributes']['HSNotes']
    if len(hs_dbn) != 0:
        for hs in hs_dbn:
            if hs != '':
                index = re.search('[a-zA-Z]', hs)
                zoned_loc_code_list.append(hs[index.start():])
    notes_list = [es_notes, ms_notes, hs_notes]
    formatted_zoned_loc_code_list = [code for code in zoned_loc_code_list]
    for code in zoned_loc_code_list:
        formatted_zoned_loc_code_list.append(code)
    return (formatted_zoned_loc_code_list, notes_list)

def get_zoned_school(zoned_loc_code_list, esri_geometry_point):
    zoned_school_payload = {
        'id': 2,
        'method': 'getSchools',
        'params': {
            'mode': 'zoned',
            'action': 'get',
            'locationCodes': zoned_loc_code_list,
            'borough': '',
            'grade': '',
            'filters': None,
            'point': {
                'type': 'point',
                'x': esri_geometry_point['x'],
                'y':  esri_geometry_point['y'],
                'spatialReference': {
                    'wkid': 102100,
                    'wkt': None,
                    '_info': {
                        '3857': {
                            'wkTemplate': "PROJCS[\"WGS_1984_Web_Mercator_Auxiliary_Sphere\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Mercator_Auxiliary_Sphere\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",${Central_Meridian}],PARAMETER[\"Standard_Parallel_1\",0.0],PARAMETER[\"Auxiliary_Sphere_Type\",0.0],UNIT[\"Meter\",1.0]]",
                            'valid': [-20037508.342788905, 20037508.342788905],
                            'origin': [-20037508.342787, 20037508.342787],
                            'dx': 0.00001
                        },
                        '4326': {
                            'wkTemplate': 'GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",${Central_Meridian}],UNIT[\"Degree\",0.0174532925199433]]',
                            'altTemplate': 'PROJCS[\"WGS_1984_Plate_Carree\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Plate_Carree\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",${Central_Meridian}],UNIT[\"Degrees\",111319.491]]',
                            'valid': [-180, 180],
                            'origin': [-180, 180],
                            'dx': 0.00001
                        },
                        '102100': {
                            'wkTemplate': 'PROJCS[\"WGS_1984_Web_Mercator_Auxiliary_Sphere\",GEOGCS[\"GCS_WGS_1984\",DATUM[\"D_WGS_1984\",SPHEROID[\"WGS_1984\",6378137.0,298.257223563]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Mercator_Auxiliary_Sphere\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",${Central_Meridian}],PARAMETER[\"Standard_Parallel_1\",0.0],PARAMETER[\"Auxiliary_Sphere_Type\",0.0],UNIT[\"Meter\",1.0]]',
                            'valid': [-20037508.342788905, 20037508.342788905],
                            'origin': [-20037508.342787, 20037508.342787],
                            'dx': 0.00001
                        },
                        '102113': {
                            'wkTemplate': 'PROJCS[\"WGS_1984_Web_Mercator\",GEOGCS[\"GCS_WGS_1984_Major_Auxiliary_Sphere\",DATUM[\"D_WGS_1984_Major_Auxiliary_Sphere\",SPHEROID[\"WGS_1984_Major_Auxiliary_Sphere\",6378137.0,0.0]],PRIMEM[\"Greenwich\",0.0],UNIT[\"Degree\",0.0174532925199433]],PROJECTION[\"Mercator\"],PARAMETER[\"False_Easting\",0.0],PARAMETER[\"False_Northing\",0.0],PARAMETER[\"Central_Meridian\",${Central_Meridian}],PARAMETER[\"Standard_Parallel_1\",0.0],UNIT[\"Meter\",1.0]]',
                            'valid': [-20037508.342788905, 20037508.342788905],
                            'origin': [-20037508.342787, 20037508.342787],
                            'dx': 0.00001
                        }
                    },
                    'declaredClass': 'esri.SpatialReference'
                },
                'declaredClass': 'esri.geometry.Point'
            },
            'sort': 0,
            'start': 0,
            'count': None
        },
        'jsonrpc': '2.0'
    }
    zoned_school_result = requests.post(ZONED_SCHOOL_URL, headers=HEADERS, json=zoned_school_payload).json()
    return zoned_school_result['result']['items']

def fetch_zoned_school_from_doe(address):
    xy_point = get_xy_point(address)
    if xy_point is None:
        print 'Address not found. Check the address ie: house number, streetname, borough'
        return []
    esri_geometry_point = get_esri_geometries_point(xy_point)
    (zoned_loc_code_list, notes_list) = get_zoned_loc_code_list(esri_geometry_point)
    zoned_schools = get_zoned_school(zoned_loc_code_list, esri_geometry_point)
    return (notes_list, zoned_schools)
