import analyzeflow

dbPath = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230216-rhc-v2.csv'
dataPath = '/home/cudmore/Sites/declan-flow-analysis-shared/data'

from analyzeflow.interface.analyzeflow_app import main
main(dbPath=dbPath, dataPath=dataPath)