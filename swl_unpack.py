import sys, json
from pydofus.swl import SWLReader, InvalidSWLFile

# python swl_unpack.py file.swl
# file output: file.swf and file.json

file = sys.argv[1]

swl_input = open(file, "rb")
swf_output = open(file.replace("swl", "swf"), "wb")
json_output = open(file.replace("swl", "json"), "w")

swl = SWLReader(swl_input)
swf_output.write(swl.SWF)
swl_data = {'version': swl.version, 'frame_rate': swl.frame_rate, 'classes': swl.classes}
json.dump(swl_data, json_output, indent=4)

swl_input.close()
swf_output.close()
json_output.close()
