import csv

class Reason(object):
	def __init__(self, input_file):
		self.file = input_file
		self.sites = self.__read_input()

	def __read_input(self):
		sites = []
		with open(self.file, 'r') as input_file:
			sites = [item for item in csv.reader(input_file, delimiter='\t')]
		input_file.close()
		return sites

	def write_changes(self, updated_sites):
		with open(self.file, 'w') as output_file:
			for row in updated_sites:
				output_file.writelines(row[0]+"\t"+str(row[1])+"\n")
		output_file.close()

