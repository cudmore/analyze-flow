# debug declan error from 20230404

import analyzeflow

# tifPath = '../../declan-flow-analysis-shared/20221102/Capillary2.tif'
tifPath = '/home/cudmore/Downloads/20230404/20230404_A18_0003.tif'

kff = analyzeflow.kymFlowFile(tifPath)

print('kff._header')
for k,v in kff._header.items():
	print('  ', k,v)


#kff.analyzeFlowWithRadon()  # do actual kym radon analysis
#kff.saveAnalysis()  # save result to csv