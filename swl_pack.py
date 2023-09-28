import sys, json
from pydofus.swl import SWLBuilder

# python swl_pack.py file.swf (require file.json)
# file output: file.swl

file = sys.argv[1]

swf_input = open(file, "rb")
json_input = open(file.replace("swf", "json"), "r")
swl_output = open(file.replace("swf", "swl"), "wb")

swl_data = json.load(json_input)
swl_data["SWF"] = swf_input.read()
swl = SWLBuilder(swl_data, swl_output)
swl.build()

swl_output.seek(0)

swl_output.close()
swf_input.close()
json_input.close()
