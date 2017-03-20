#!/usr/bin/python
# convert a xlsx file to github wiki in table view
import csv
import xlrd

workbook = xlrd.open_workbook(r'test.xlsx')
sheet = workbook.sheet_by_index(0)
nrows = sheet.nrows
ncols = sheet.ncols
with open('result.txt', 'w') as writefile:
	header = False
	for row in range(0, nrows):
		data = sheet.row_values(row)
		for i in range(len(data)):
			if data[i] == u'':
				data[i] = data[i].replace(u'', u' ')
		writefile.write('|' + '|'.join(data) + ' |\n')
		if header == False:
			header = True
			splitMark = ''
			for i in range(0, ncols):
				splitMark = splitMark + '| ------ '
			writefile.write(splitMark + ' |\n')