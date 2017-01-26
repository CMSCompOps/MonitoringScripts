import csv

class Log(object):
	def __init__(self, input_file):
		self.file = input_file
		self.records = self.read_input()

	def read_input(self):
		with open(self.file, 'r') as input_file:
			records = [item for item in csv.reader(input_file, delimiter='\t')]
		input_file.close()
		return records

	def write_changes(self, new_record):
		self.records.insert(0, new_record)
		with open(self.file, 'w') as output_file:
			for row in self.records:
				output_file.writelines(row[0]+"\t"+row[1]+"\t"+row[2]+"\t"+row[3]+"\t"+row[4]+"\n")
		output_file.close()
