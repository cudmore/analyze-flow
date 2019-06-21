"""
	Author: Robert H. Cudmore
	Date: 20160815
	Email: robert.cudmore@gmail.com
	Web: http://robertcudmore.org
	Github: https://github.com/cudmore/bob-fiji-plugins

	This script will convert a directory of image files into single channel .tif files.
	The output .tif files can then be imported into MapManager.
	All output .tif files go into new folder /src/src_tif where /src/ is the directory you specify
	This script should work for:
		- Zeiss lsm/czi
		- ScanImage 3 .tif files
		- Not sure about other formats ???
		
	If you need a slightly different converter for your specific files, please email Robert Cudmore.
	We will extend this to ScanImage 4, please email for updates.

	The name of this file must end in an underscore, '_'. Otherwise Fiji will not install it as a plugin.

	Options:
		1) magic_scan_image_scale
			For ScanImage files, set magic_scan_image_scale. If you do not do this the scale WILL BE WRONG
		2) date_order
			Check the date format on the computer you are using to acquire images and set date_order appropriately.
	
	Change Log:
		20170810: Updated to handle __name__ == __builtin__
		20170811: added acceptedExtensions = ['.lsm', '.tif']
		20170811: Should now work with ScanImage 3
		20170812: Now handles Zeiss .czi files. Date, time, zoom, and voxel size should all be correct	
		20180626: Adding support for Nikon nd2 files (Hao Wu, Tianjin University)	
		20190302: Adding support for Olympus oir files
			- Now saving .txt file for each converted Tiff for easy import into Matlab FocusStack scripts
			- todo: when we save one channel, it is actually Olympus channel 2 (green)
			- todo: when we save 2 channels they will be _ch1:red, _ch2:green
			
"""

import os, time, math
from collections import OrderedDict

from ij import IJ
from ij import ImagePlus # davis
from ij import WindowManager
from ij.io import DirectoryChooser, FileSaver, Opener, FileInfo
from ij.plugin import ZProjector

# 20190302 davis
from ij.process import ImageConverter # default convert to 8-bit will scale. Turn it off. See: https://ilovesymposia.com/2014/02/26/fiji-jython/
from ij.process import StackStatistics

from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.formats import ImageReader
from loci.formats import MetadataTools


##################################################################################################
# Options
##################################################################################################

# This number specifies the voxel size (um) for ScanImage .tif files at 1024x1024, zoom=1
# voxelx and voxely = magic_scan_image_scale / zoom
# If this is not set correctly (for your scope) then the output voxels will be WRONG
magic_scan_image_scale = 0.54

# Folders that are converted to Map Manager should all be following the same date format.
# If they are heterogeneous in their date formats, split your raw tif/lsm/czi files into different folders.
# Set the format for a folder and run this script, repeat on other foder and then manually merge output
date_order = 'mmddyyyy' # possible values here are: yyyymmdd, mmddyyyy, ddmmyyyy
date_order = 'yyyymmdd' # johns czi files (core computers are set up this way?)

gConvertTo8Bit = False # added 20190302 davis
gSaveSingleImage = True # davis, max project across moving tseries was giving us all max pixels in max project

gSaveImages = False # davis, option to NOT save images, allows to only save header

# For ScanImage negative intensities
gRemoveCalibration = True # only is self.scanImageVersion
gForceRemoveCalibration = True
gLinearShift = math.pow(2,15) - 128

###
# End Options
###

#versionStr = '0.1' # 20170813: first version, I don't think anybody used this
versionStr = '0.0.1' # 20180626: second version

##################################################################################################
class bImp:
	def removeCalibration(self):
		if gRemoveCalibration and self.scanImageVersion:
			cal = self.imp.getCalibration()
			calCoeff = cal.getCoefficients()
			if gForceRemoveCalibration or calCoeff:
				if calCoeff:
					msgStr = 'Calibration is y=a+bx' + ' a=' + str(calCoeff[0]) + ' b=' + str(calCoeff[1])
					bPrintLog(msgStr, 3)
				
				#remove calibration
				bPrintLog('Removing Calibration', 3)
				self.imp.setCalibration(None)
					
				#without these, 8-bit conversion goes to all 0 !!! what the fuck !!!
				#bPrintLog('calling imp.resetStack() and imp.resetDisplayRange()', 2)
				self.imp.resetStack()
				self.imp.resetDisplayRange()
	
				#get and print out min/max
				origMin = StackStatistics(self.imp).min
				origMax = StackStatistics(self.imp).max
				msgStr = 'orig min=' + str(origMin) + ' max=' + str(origMax)
				bPrintLog(msgStr, 4)

				if origMin >= 0:
					bPrintLog('Did not remove calibration, all pixel intensities are >=0', 4)
					return 1
					
				# 20150723, 'shift everybody over by linear calibration intercept calCoeff[0] - (magic number)
				if 1:
					# [1] was this
					#msgStr = 'Subtracting original min '+str(origMin) + ' from stack.'
					#bPrintLog(msgStr, 2)
					#subArgVal = 'value=%s stack' % (origMin,)
					#IJ.run('Subtract...', subArgVal)
					# [2] now this
					#msgStr = 'Adding calCoeff[0] '+str(calCoeff[0]) + ' from stack.'
					#bPrintLog(msgStr, 2)
					#addArgVal = 'value=%s stack' % (int(calCoeff[0]),)
					#IJ.run('Add...', addArgVal)
					# [3] subtract a magic number 2^15-2^7 = 32768 - 128
					magicNumber = gLinearShift #2^15 - 128
					msgStr = 'Subtracting a magic number (linear shift) '+str(magicNumber) + ' from stack.'
					bPrintLog(msgStr, 4)
					self.infoStr += 'bLinearShift=' + str(gLinearShift) + '\n'
					subArgVal = 'value=%s stack' % (gLinearShift,)
				IJ.run(self.imp, 'Subtract...', subArgVal)
				
				# 20150701, set any pixel <0 to 0
				if 0:
					ip = self.imp.getProcessor() # returns a reference
					pixels = ip.getPixels() # returns a reference
					msgStr = '\tSet all pixels <0 to 0. This was added 20150701 ...'
					bPrintLog(msgStr, 2)
					pixels = map(lambda x: 0 if x<0 else x, pixels)
					bPrintLog('\t\t... done', 2)
				
				#get and print out min/max
				newMin = StackStatistics(self.imp).min
				newMax = StackStatistics(self.imp).max
				msgStr = 'new min=' + str(newMin) + ' max=' + str(newMax)
				bPrintLog(msgStr, 4)
			
				#append calibration to info string
				if calCoeff:
					self.infoStr += 'bCalibCoeff_a = ' + str(calCoeff[0]) + '\n'
					self.infoStr += 'bCalibCoeff_b = ' + str(calCoeff[1]) + '\n'
				self.infoStr += 'bNewMin = ' + str(newMin) + '\n'
				self.infoStr += 'bNewMax = ' + str(newMax) + '\n'

	def __init__(self, filepath):
		"""
		Load an image or stack from filepath.

		Args:
			filepath (str): Full path to an image file. Can be .tif, .lsm, .czi, etc
		"""
		
		if not os.path.isfile(filepath):
			bPrintLog('ERROR: bImp() did not find file: ' + filepath,0)
			return 0

		self.filepath = filepath
		folderpath, filename = os.path.split(filepath)
		self.filename = filename
		self.enclosingPath = folderpath
		self.enclosingfolder = os.path.split(folderpath)[1]

		self.dateStr = ''
		self.timeStr = ''
		
		self.imp = None
		
		tmpBaseName, extension = os.path.splitext(filename)
		isZeiss = extension in ['.czi', '.lsm']
		self.islsm = extension == '.lsm'
		self.isczi = extension == '.czi'
		istif = extension == '.tif'
		isnd2 = extension == '.nd2'
		isoir = extension == '.oir'

		if istif:
			# scanimage3 comes in with dimensions: [512, 512, 1, 52, 1]) = [width, height, numChannels, numSlices, numFrames]
			
			# 20190516, was not working for Yong ScanImage 5 tif files?
			'''
			self.imp = Opener().openImage(filepath)
			self.imp.show()
			'''
			options = ImporterOptions()
			options.setId(filepath)
			imps = BF.openImagePlus(options)
			for imp in imps:
				self.imp = imp #WindowManager.getImage(self.windowname)
				imp.show()
			
		elif isZeiss:
			#open lsm using LOCI Bio-Formats
			options = ImporterOptions()
			#options.setColorMode(ImporterOptions.COLOR_MODE_GRAYSCALE)
			options.setId(filepath)
			imps = BF.openImagePlus(options)
			for imp in imps:
				self.imp = imp #WindowManager.getImage(self.windowname)
				imp.show()

		elif isnd2 or isoir:
			
			options = ImporterOptions()
			options.setId(filepath)

			# this shows xml meta data in window
			#options.setShowMetadata(True)
			#options.setShowOMEXML(True)
			
			imps = BF.openImagePlus(options)

			for imp in imps:
				self.imp = imp #WindowManager.getImage(self.windowname)
				imp.show()
		
		if not self.imp:
			bPrintLog('ERROR: bImp() was not able to open file: '+ filepath,0)

		self.windowname = filename
		#self.imp = WindowManager.getImage(self.windowname)

		# numChannels is not correct for scanimage, corrected in readTiffHeader()
		(width, height, numChannels, numSlices, numFrames) = self.imp.getDimensions()

		self.width = width # pixelsPerLine
		self.height = height # linesPerFrame
		self.numChannels = numChannels
		self.numSlices = numSlices
		self.numFrames = numFrames

		self.infoStr = self.imp.getProperty("Info") #get all tags
		# 20180703, sometimes .tif files have None infoStr ???
		if self.infoStr is None:
			self.infoStr = ''

		# added while working on Plympus (I am mimiking Prairie format/name so Matlab FocusStack works
		self.sequenceType = 'None'

		self.scannerType = '' # added for olympus ('Resonant', 'Galvano')
		
		self.voxelx = 1
		self.voxely = 1
		self.voxelz = 1
		#self.numChannels = 1
		#self.bitsPerPixel = 8
		self.zoom = None

		self.motorx = None
		self.motory = None
		self.motorz = None

		self.scanImageVersion = '' # if set we will try to remove calibration
		self.msPerLine = None
		self.dwellTime = None

		self.bitDepth = None # 20180626, Hao Wu
		self.framePeriod = None # 20180626, Hao Wu
		self.lineSpeed = None # 20190524, Olympus
		self.dwellTime = None # 20180626, Hao Wu

		#self.bitsPerPixel = None

		# laser
		self.laserWaveLength = None
		self.laserPercentPower = None

		#pmt 1
		self.pmtVoltage1 = None
		self.pmtOffset1 = None
		self.pmtGain1 = None
		#pmt 2
		self.pmtVoltage2 = None
		self.pmtOffset2 = None
		self.pmtGain2 = None
		# pmt 3
		self.pmtVoltage3 = None
		self.pmtOffset3 = None
		self.pmtGain3 = None
		
		# read file headers (date, time, voxel size)
		if isZeiss:
			self.readZeissHeader(self.infoStr)
		elif istif:
			self.readTiffHeader(self.infoStr)
		elif isnd2:
			self.readNikonHeader(self.infoStr)
		elif isoir:
			self.readOlympusHeader(self.infoStr)
			
		self.removeCalibration()
		
		self.updateInfoStr()

		self.channelWindows = []
		self.channelImp = []
		
		if self.numChannels == 1:
			self.channelWindows.append(self.windowname)
			self.channelImp.append(self.imp)
		else:
			self.deinterleave()
			
	###################################################################################
	def updateInfoStr(self):
		"""
		Fill in infoStr with Map Manager tags		
		
		Todo: Add
			b_bitDepth, b_opticalZoom, b_dwellTime, b_scanlinePeriod, b_framePeriod
		"""
		
		self.infoStr += 'Folder2MapManager=' + versionStr + '\n'

		self.infoStr += 'b_date=' + self.dateStr + '\n'
		self.infoStr += 'b_time=' + self.timeStr + '\n'

		# 20190302 davis
		self.infoStr += 'b_sequence=' + self.sequenceType + '\n'

		if self.scannerType:
			self.infoStr += 'b_scannerType=' + self.scannerType + '\n'
			
		# yevgeniya 20180314
		#if (self.numChannels > 3):
		#	self.numChannels = 3
		self.infoStr += 'b_numChannels=' + str(self.numChannels) + '\n'
		self.infoStr += 'b_pixelsPerline=' + str(self.width) + '\n'
		self.infoStr += 'b_linesPerFrame=' + str(self.height) + '\n'
		self.infoStr += 'b_numSlices=' + str(self.numSlices) + '\n'
		
		self.infoStr += 'b_voxelX=' + str(self.voxelx) + '\n'
		self.infoStr += 'b_voxelY=' + str(self.voxely) + '\n'
		self.infoStr += 'b_voxelZ=' + str(self.voxelz) + '\n'

		#self.infoStr += 'b_bitsPerPixel=' + str(self.bitsPerPixel) + '\n'

		if self.zoom is not None:
			self.infoStr += 'b_zoom=' + str(self.zoom) + '\n'
		
		# 20190516, changed from b_motorx to b_xMotor to match MapManager Igor ???
		'''
		self.infoStr += 'b_motorx=' + str(self.motorx) + '\n'
		self.infoStr += 'b_motory=' + str(self.motory) + '\n'
		self.infoStr += 'b_motorz=' + str(self.motorz) + '\n'
		'''
		self.infoStr += 'b_xMotor=' + str(self.motorx) + '\n'
		self.infoStr += 'b_yMotor=' + str(self.motory) + '\n'
		self.infoStr += 'b_zMotor=' + str(self.motorz) + '\n'

		self.infoStr += 'b_msPerLine=' + str(self.msPerLine) + '\n'

		if self.scanImageVersion:
			self.infoStr += 'b_scanImageVersion=' + self.scanImageVersion + '\n'

		if self.bitDepth is not None:
			self.infoStr += 'b_bitDepth=' + str(self.bitDepth) + '\n'

		if self.framePeriod is not None:
			self.infoStr += 'b_framePeriod=' + str(self.framePeriod) + '\n'
		
		if self.lineSpeed is not None:
			self.infoStr += 'b_lineSpeed=' + str(self.lineSpeed) + '\n'
		
		if self.dwellTime is not None:
			self.infoStr += 'b_dwellTime=' + str(self.dwellTime) + '\n'

		# added while working on Olympus
		if self.laserWaveLength is not None:
			self.infoStr += 'b_laserWaveLength=' + str(self.laserWaveLength) + '\n'
		if self.laserPercentPower is not None:
			self.infoStr += 'b_laserPercentPower=' + str(self.laserPercentPower) + '\n'

		# pmt1
		if self.pmtVoltage1 is not None:
			self.infoStr += 'b_pmtVoltage1=' + str(self.pmtVoltage1) + '\n'
		if self.pmtOffset1 is not None:
			self.infoStr += 'b_pmtOffset1=' + str(self.pmtOffset1) + '\n'
		if self.pmtGain1 is not None:
			self.infoStr += 'b_pmtGain1=' + str(self.pmtGain1) + '\n'
		# pmt2
		if self.pmtVoltage2 is not None:
			self.infoStr += 'b_pmtVoltage2=' + str(self.pmtVoltage2) + '\n'
		if self.pmtOffset2 is not None:
			self.infoStr += 'b_pmtOffset2=' + str(self.pmtOffset2) + '\n'
		if self.pmtGain2 is not None:
			self.infoStr += 'b_pmtGain2=' + str(self.pmtGain2) + '\n'
		# pmt1
		if self.pmtVoltage3 is not None:
			self.infoStr += 'b_pmtVoltage3=' + str(self.pmtVoltage3) + '\n'
		if self.pmtOffset3 is not None:
			self.infoStr += 'b_pmtOffset3=' + str(self.pmtOffset3) + '\n'
		if self.pmtGain3 is not None:
			self.infoStr += 'b_pmtGain3=' + str(self.pmtGain3) + '\n'

		
	###################################################################################
	def saveHeaderFile(self):
		"""
		Save a .txt file with detection parameters
		Return a dictionary of key/value detection parameters
		"""

		retDict = OrderedDict()
		
		# make output folder if necc
		# todo: put this is constructor, it is spread between *here, saveTiffStack, saveMaxProject ...
		destFolder = os.path.join(self.enclosingPath, self.enclosingfolder + '_tif')
		if not os.path.isdir(destFolder):
			os.makedirs(destFolder)

		tmpBaseName, extension = os.path.splitext(self.filename)
		
		dstTextFile = os.path.join(destFolder, tmpBaseName + '.txt')

		#
		# first put everything into a dict
		
		#with open(dstTextFile, 'w') as f:

		retDict['file'] = self.filename
		
		#f.write('date=' + str(self.dateStr) + '\n')
		#f.write('time=' + str(self.timeStr) + '\n')
		retDict['date'] = str(self.dateStr)
		retDict['time'] = str(self.timeStr)

		# laser
		'''
		if self.laserWaveLength is not None:
			f.write('laserWaveLength=' + str(self.laserWaveLength) + '\n')
		if self.laserPercentPower is not None:
			f.write('laserPercentPower=' + str(self.laserPercentPower) + '\n')
		'''
		retDict['laserWaveLength'] = str(self.laserWaveLength)
		retDict['laserPercentPower'] = str(self.laserPercentPower)
			
		# todo: convert bitDepth to bitsPerPixel
		#f.write('bitsPerPixel=' + str(self.bitDepth) + '\n')
		retDict['bitsPerPixel'] = str(self.bitDepth)

		#f.write('zoom=' + str(self.zoom) + '\n')
		retDict['zoom'] = str(self.zoom)
			
		#f.write('sequence=' + str(self.sequenceType) + '\n')
		#f.write('scannerType=' + str(self.scannerType) + '\n')
		retDict['sequence'] = str(self.sequenceType)
		retDict['scannerType'] = str(self.scannerType)
		
		#f.write('framePeriod=' + str(self.framePeriod) + '\n')
		#f.write('lineSpeed=' + str(self.lineSpeed) + '\n')
		#f.write('dwellTime=' + str(self.dwellTime) + '\n')
		retDict['framePeriod'] = str(self.framePeriod)
		retDict['lineSpeed'] = str(self.lineSpeed)
		retDict['dwellTime'] = str(self.dwellTime)
			
		#f.write('voxelx=' + str(self.voxelx) + '\n')
		#f.write('voxely=' + str(self.voxely) + '\n')
		#f.write('voxelz=' + str(self.voxelz) + '\n')
		retDict['voxelx'] = str(self.voxelx)
		retDict['voxely'] = str(self.voxely)
		retDict['voxelz'] = str(self.voxelz)
			
		#f.write('numSlices=' + str(self.numSlices) + '\n')
		#f.write('numFrames=' + str(self.numFrames) + '\n')
		retDict['numSlices'] = str(self.numSlices)
		retDict['numFrames'] = str(self.numFrames)
			
		#f.write('pixelsPerLine=' + str(self.width) + '\n')
		#f.write('linesPerFrame=' + str(self.height) + '\n')
		retDict['pixelsPerLine'] = str(self.width)
		retDict['linesPerFrame'] = str(self.height)
			
		# pmt 1
		#if self.pmtVoltage1 is not None:
		#	f.write('pmtVoltage1=' + str(self.pmtVoltage1) + '\n')
		retDict['pmtVoltage1'] = str(self.pmtVoltage1)
		#if self.pmtOffset1 is not None:
		#	f.write('pmtOffset1=' + str(self.pmtOffset1) + '\n')
		retDict['pmtOffset1'] = str(self.pmtOffset1)
		#if self.pmtGain1 is not None:
		#	f.write('pmtGain1=' + str(self.pmtGain1) + '\n')
		retDict['pmtGain1'] = str(self.pmtGain1)
			
		# pmt 2
		#if self.pmtVoltage2 is not None:
		#	f.write('pmtVoltage2=' + str(self.pmtVoltage2) + '\n')
		retDict['pmtVoltage2'] = str(self.pmtVoltage2)
		#if self.pmtOffset2 is not None:
		#	f.write('pmtOffset2=' + str(self.pmtOffset2) + '\n')
		retDict['pmtOffset2'] = str(self.pmtOffset2)
		#if self.pmtGain2 is not None:
		#	f.write('pmtGain2=' + str(self.pmtGain2) + '\n')
		retDict['pmtGain2'] = str(self.pmtGain2)
		# pmt 1
		#if self.pmtVoltage3 is not None:
		#	f.write('pmtVoltage3=' + str(self.pmtVoltage3) + '\n')
		retDict['pmtVoltage3'] = str(self.pmtVoltage3)
		#if self.pmtOffset3 is not None:
		#	f.write('pmtOffset3=' + str(self.pmtOffset3) + '\n')
		retDict['pmtOffset3'] = str(self.pmtOffset3)
		#if self.pmtGain3 is not None:
		#	f.write('pmtGain3=' + str(self.pmtGain3) + '\n')
		retDict['pmtGain3'] = str(self.pmtGain3)
			
		#
		# write the dict to a file
		with open(dstTextFile, 'w') as f:
			for k,v in retDict.items():
				#print(k,v)
				f.write(k + "=" + str(v) + '\n')
				
		return retDict
		
	###################################################################################
	def readOlympusHeader(self, infoStr):
		"""
		Read Olympus oir file header

		Scan can be either ('Resonant' or 'Galvano'
			For Resonant, read from #3
			For Galvano read from #2
		"""

		print('readOlympusHeader infoStr')
		
		for line in infoStr.split('\n'):
			if line.find('fileInfomation version #1') != -1:
				bPrintLog('Found file version: ' + line, 3)
			if line.find('system systemVersion #1') != -1:
				bPrintLog('Found system version: ' + line, 3)

			if line.find('general creationDateTime #1') != -1:
				bPrintLog('creationDateTime: ' + line, 3)
				rhs = line.split('= ')[1]
				self.dateStr, self.timeStr = rhs.split('T')
				self.dateStr = bFixDate(self.dateStr)
				self.timeStr = bFixTime(self.timeStr)
				#print('self.dateStr:', self.dateStr)
				#print('self.timeStr:', self.timeStr)
				
			# type of scan in ('TIMELAPSE, 'ZSTACK')
			if line.find('axisValue axisType #1') != -1:
				bPrintLog('axisValue axisType #1: ' + line, 3)
				rhs = line.split('= ')[1] # space is intentional
				rhs = str(rhs)
				if rhs=='TIMELAPSE': # preceding space is intentional
					self.sequenceType = 'TSeries'
				elif rhs=='ZSTACK': # preceding space is intentional
					self.sequenceType = 'ZStack'
				else:
					print('ERROR: unknown sequence type rhs=', rhs)
					
			# in ('Galvano', 'Resonant')
			if line.find('configuration scannerType #1') != -1:
				rhs = line.split('= ')[1] # space is intentional
				rhs = str(rhs)
				self.scannerType = rhs
				#bPrintLog(line, 3)

			# image width/height (pixels)
			'''
			if line.find('imageDefinition width #1') != -1:
				bPrintLog(line, 3)
			if line.find('imageDefinition height #1') != -1:
				bPrintLog(line, 3)
			'''
			
			# frame count
			# synchronizedAcquisitionParamList imagingFrameCount #1 = 1000
			'''
			if line.find('synchronizedAcquisitionParamList imagingFrameCount #1') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				#self.numSlices = rhs
			'''
			
			# frame period
			if line.find('speedInformation frameSpeed #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Galvano':
					self.framePeriod = rhs
			if line.find('speedInformation frameSpeed #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Resonant':
					self.framePeriod = rhs
				
			# line speed
			if line.find('speedInformation lineSpeed #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Galvano':
					self.lineSpeed = rhs
			if line.find('speedInformation lineSpeed #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Resonant':
					self.lineSpeed = rhs
				
			# line speed
			if line.find('speedInformation pixelSpeed #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Galvano':
					self.dwellTime = rhs
			if line.find('speedInformation pixelSpeed #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				if self.scannerType == 'Resonant':
					self.dwellTime = rhs
				
			# zoom
			if line.find('area zoom #1') != -1:
				#bPrintLog('zoom: ' + line, 3)
				rhs = line.split('= ')[1]
				self.zoom = rhs

			'''
			if line.find('zPositiontem') != -1:
				bPrintLog('zPosition: ' + line, 3)
			'''
			
			# voxel size
			if line.find('length x #1') != -1:
				#bPrintLog('voxelx: ' + line, 3)
				rhs = line.split('= ')[1]
				self.voxelx = rhs
			if line.find('length y #1') != -1:
				#bPrintLog('voxely: ' + line, 3)
				rhs = line.split('= ')[1]
				self.voxely = rhs
			if line.find('length z #1') != -1:
				#bPrintLog('voxelz: ' + line, 3)
				rhs = line.split('= ')[1]
				self.voxelz = rhs

			#
			# ADD THESE TO SELF
			#
			
			# laser wavelength
			if line.find('stimulationMainLaser wavelength #1') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.laserWaveLength = rhs
			# laser percent power
			if line.find('Laser Chameleon Vision II transmissivity') != -1:
				#bPrintLog('Laser % Power: ' + line, 3)
				rhs = line.split('= ')[1]
				self.laserPercentPower = rhs
			
			# bits per pixel
			if line.find('imageDefinition bitCounts #1') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.bitDepth = rhs
			
			# pmt 1
			if line.find('pmt voltage #1') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtVoltage1 = rhs
			if line.find('pmt offset #1') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtOffset1 = rhs
			if line.find('pmt gain #1') != -1:
				bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtGain1 = rhs
			# pmt 2
			if line.find('pmt voltage #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtVoltage2 = rhs
			if line.find('pmt offset #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtOffset2 = rhs
			if line.find('pmt gain #2') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtGain2 = rhs
			# pmt 3
			if line.find('pmt voltage #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtVoltage3 = rhs
			if line.find('pmt offset #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtOffset3 = rhs
			if line.find('pmt gain #3') != -1:
				#bPrintLog(line, 3)
				rhs = line.split('= ')[1]
				self.pmtGain3 = rhs
			
				
			# responant mode, frame period might be
			#speedInformation frameSpeed #3 = 33.33333333333333
			
			
			# axisValue axisType #1 = TIMELAPSE
			# axisValue axisType #1 = ZSTACK
			# imagingMainLaser wavelength #1
			# configuration scannerType #1 = Resonant
			# configuration scannerType #1 = Galvano

			'''
			speedInformation frameSpeed #1 = 412.742
			speedInformation frameSpeed #2 = 172.458
			speedInformation frameSpeed #3 = 33.33333333333333
			speedInformation lineSpeed #1 = 1.606
			speedInformation lineSpeed #2 = 1.474
			speedInformation lineSpeed #3 = 0.06337135614702154
			speedInformation pixelSpeed #1 = 0.002
			speedInformation pixelSpeed #2 = 0.002
			speedInformation pixelSpeed #3 = 6.7E-5
			speedInformation seriesInterval #1 = 172.458
			speedInformation seriesInterval #2 = 33.33333333333333
			'''
		print('\n')
		
	###################################################################################
	def readNikonHeader(self, infoStr):
		"""
		Read Nikon nd2 file header
		"""
		
		# for nd2 file, infoStr is completely useless
		#print 'infoStr:', infoStr
				
		# see: http://downloads.openmicroscopy.org/bio-formats/5.0.3/api/ome/xml/meta/MetadataRetrieve.html
		# see: https://gist.github.com/ctrueden/6282856
		
		reader = ImageReader()
		omeMeta = MetadataTools.createOMEXMLMetadata() #return IMetadata, usage is omeMeta.getImageAcquisitionDate(0)
		reader.setMetadataStore(omeMeta)
		reader.setId(self.filepath)
		
		#dateTimeStr = omeMeta.getImageAcquisitionDate(0) #return None
		#print 'dateTimeStr:', dateTimeStr
		"""
		the info string has some wierd date that is different from python getctime/getmtime
		TextInfoItem_92018/6/2 = 11:52:39
		"""
		#
		# mtime may vary if this script is run on OSX versus Windows?
		ctime = os.path.getctime(self.filepath)
		mtime = os.path.getmtime(self.filepath)
		#print 'c date/time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime)) # this is when I copied to my computer
		#print 'm date/time:', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime)) # this one is better?
		
		#
		# The date does not appear to be in the file
		# I am choosing here to NOT try reading creation/modification date/time as this is not reliable
		#bPrintLog('readNikonHeader() is using os.path.getmtime(path) for date/time (this might be wrong)', 3)
		#self.dateStr = time.strftime('%Y%m%d', time.localtime(mtime))
		#self.timeStr = time.strftime('%H:%M:%S', time.localtime(mtime))

		#bPrintLog('Using modification time:' + self.dateStr + ' ' + self.timeStr)

		#tmpDateStr = time.strftime('%Y%m%d', time.localtime(ctime))
		#tmpTimeStr = time.strftime('%H:%M:%S', time.localtime(ctime))
		#bPrintLog('Using modification time WOULD BE:' + tmpDateStr + ' ' + tmpTimeStr)
		
		#seriesCount = reader.getSeriesCount() # this returns 1
		#print 'seriesCount:', seriesCount
		
		#print 'omeMeta.getPixelsSizeX():', omeMeta.getPixelsSizeX(0) # 512
		#print 'omeMeta.getPixelsSizeY():', omeMeta.getPixelsSizeY(0) # 512
		#print 'omeMeta.getPixelsSizeZ():', omeMeta.getPixelsSizeZ(0) #
		#self.width = omeMeta.getPixelsSizeX(0) # set once we load actual image in constructor
		#self.height = omeMeta.getPixelsSizeY(0) # set once we load actual image in constructor
		
		#print 'omeMeta.getImageCount():', omeMeta.getImageCount() # returns 1
		
		#datasetCount = omeMeta.getDatasetCount() # returns 0
		#print 'datasetCount:', datasetCount
		
		#experimentCount = omeMeta.getExperimentCount() # returns 0
		#print 'experimentCount:', experimentCount

		#uuid = omeMeta.getUUID() # return None
		#print 'uuid:', uuid
		
		#channelCount = omeMeta.getChannelCount(0)
		#print 'channelCount:', channelCount
		#self.numChannels = channelCount # set once we load actual image in constructor
		
		bitDepth = omeMeta.getPixelsSignificantBits(0) # returns positive integer
		#print 'bitDepth:', bitDepth
		if bitDepth>1:
			self.bitDepth = bitDepth
			
		if 0:
			# not sure what this gives me?
			planeDeltaT = omeMeta.getPlaneDeltaT(0,0) # image period ????
			if planeDeltaT is not None:
				print 'planeDeltaT:', planeDeltaT.value(), planeDeltaT.unit().getSymbol()
				self.framePeriod = omeMeta.getPixelsSizeT(0)
			else:
				print 'ERROR: readNikonHeader() planeDeltaT is None'

		#pixelsTimeIncrement = omeMeta.getPixelsTimeIncrement(0) # nd2 returns None
		#print 'pixelsTimeIncrement:', pixelsTimeIncrement

		if 0:
			# not sure what this gives me?
			pixelsSizeT = omeMeta.getPixelsSizeT(0) # returns positive integer, dwell time in ns?
			print 'pixelsSizeT:', pixelsSizeT
			if pixelsSizeT>1:
				self.dwellTime = pixelsSizeT
		
		# returns: ome.units.quantity.Length: value[0.12429611388044776], unit[µm] stored as java.lang.Double
		#
		physSizeX = omeMeta.getPixelsPhysicalSizeX(0) #
		if physSizeX is not None:
			self.voxelx = physSizeX.value()
			#print 'physSizeX:', str(physSizeX.value()), physSizeX.unit().getSymbol() 
		else:
			print 'ERROR: readNikonHeader() physSizeX is None'
		#
		physSizeY = omeMeta.getPixelsPhysicalSizeY(0) #
		if physSizeY is not None:
			self.voxely = physSizeY.value()
			#print 'physSizeY:', str(physSizeY.value()), physSizeY.unit().getSymbol()
		else:
			print 'ERROR: readNikonHeader() physSizeY is None'
		#
		physSizeZ = omeMeta.getPixelsPhysicalSizeZ(0) #
		if physSizeZ is not None:
			self.voxelz = physSizeZ.value()
			print 'physSizeZ:', str(physSizeZ.value()), physSizeZ.unit().getSymbol()
		else:
			#print 'ERROR: readNikonHeader() physSizeZ is None'
			pass
				
		reader.close()

		
	###################################################################################
	def readTiffHeader(self, infoStr):
		"""
		Read both generic tiff and ScanImage 3/4 .tif headers
		"""
		
		if infoStr is None:
			bPrintLog('ERROR: readTiffHeader got None infoStr')
			return 0
			
		logLevel = 3

		# splitting on '\r' for scanimage 3.x works
		# splitting on '\n' for scanimage 4.x works
		
		#we need to search whole infoStr to figure out scanimage 3 or 4.
		# we can't split info string because si3 uses \r and si4 uses \n
		
		infoStrDelim = '\n'
		if infoStr.find('scanimage.SI4') != -1:
			infoStrDelim = '\n'
			bPrintLog('Assuming SI4 infoStr to be delimited with backslash n', logLevel)
		elif infoStr.find('state.software.version') != -1:
			infoStrDelim = '\r'
			bPrintLog('Assuming SI3 infoStr to be delimited with backslash r', logLevel)
		else:
			bPrintLog('Splitting infoStr using backslash n', logLevel)

		# if we don't find zoom then voxel is an error (see end of function)
		foundZoom = False
		
		self.scanImageVersion = ''
		
		#for line in infoStr.split('\n'):
		for line in infoStr.split(infoStrDelim):
			# debugging
			#print 'infoStr:', infoStr
			
			#
			# ScanImage 5.x
			#
			if line.find('SI.VERSION_MAJOR') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.scanImageVersion = rhs

			# SI.hMotors.motorPosition = [4121.13 6312.13 533]
			if line.find('SI.hMotors.motorPosition ') != -1: # space ' ' at end is important
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				floats = [float(x) for x in rhs.split()]
				self.motorx = floats[0]
				self.motory = floats[1]
				self.motorz = floats[2]

			# SI.hChannels.channelSave = [1;2]
			if line.find('SI.hChannels.channelSave') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				channels = [int(x) for x in rhs.split(';')]
				bPrintLog('reading SI.hChannels.channelSave inferred channels:' + str(channels), logLevel)
				self.numChannels = len(channels)
			
			# SI.hRoiManager.scanZoomFactor = 2
			if line.find('SI.hRoiManager.scanZoomFactor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.zoom = float(rhs)
				foundZoom = True
				#self.voxelx = magic_scan_image_scale / self.zoom
				#self.voxely = magic_scan_image_scale / self.zoom

			# SI.hScan2D.channelsAdcResolution = 14

			#SI.hRoiManager.scanFramePeriod = 0.0658459
			if line.find('I.hRoiManager.scanFramePeriod') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.framePeriod = float(rhs)
			
			#
			# date time is not in the header, wtf ScanImage people !!!
			#
			
			# ScanImage 4.x
			#
			
			# scanimage.SI4.versionMajor = 4.2
			if line.find('scanimage.SI4.versionMajor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.scanImageVersion = rhs
			
			# scanimage.SI4.motorPosition = [-33936.5 -106316 -55308.5]
			if line.find('scanimage.SI4.motorPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				floats = [float(x) for x in rhs.split()]
				self.motorx = floats[0]
				self.motory = floats[1]
				self.motorz = floats[2]

			# scanimage.SI4.channelsSave = [1;2]
			if line.find('scanimage.SI4.channelsSave') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				channels = [int(x) for x in rhs.split(';')]
				bPrintLog('reading scanimage.SI4.channelsSave inferred channels:' + str(channels), logLevel)
				self.numChannels = len(channels)

			# scanimage.SI4.scanZoomFactor = 5.9
			if line.find('scanimage.SI4.scanZoomFactor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.zoom = float(rhs)
				foundZoom = True
				#self.voxelx = magic_scan_image_scale / self.zoom
				#self.voxely = magic_scan_image_scale / self.zoom

			# scanimage.SI4.triggerClockTimeFirst = '18-05-2015 11:58:43.788'
			if line.find('scanimage.SI4.triggerClockTimeFirst') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace("'","") # remove enclosing ' and '
				if rhs.startswith(' '): # if date string starts with space, remove it
					rhs = rhs[1:-1]
				datetime = rhs.split(' ')
				# 20170811, there is an extra fucking space before datestr on the rhs
				# convert mm/dd/yyyy to yyyymmdd
				#print 'rhs:' + "'" + rhs + "'"
				#print 'datetime:', datetime
				datestr = bFixDate(datetime[0], logLevel)
				self.dateStr = datestr
				self.timeStr = datetime[1]
			
			#
			# ScanImage 3.x
			#
			
			# state.software.version = 3.8
			if line.find('state.software.version') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.scanImageVersion = rhs
			
			# state.acq.numberOfChannelsAcquire = 2
			if line.find('state.acq.numberOfChannelsAcquire') != -1:
				#print '\rDEBUG 12345'
				bPrintLog(line, logLevel)
				#print '\rDEBUG 12345'
				rhs = line.split('=')[1]
				self.numChannels = int(rhs)

			# state.acq.zoomFactor = 2.5
			if line.find('state.acq.zoomFactor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.zoom = float(rhs)
				foundZoom = True
				# set (voxelx, voxely)
				#self.voxelx = magic_scan_image_scale / self.zoom
				#self.voxely = magic_scan_image_scale / self.zoom
				
			# state.acq.msPerLine = 2.32
			if line.find('state.acq.msPerLine') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.msPerLine = float(rhs)
			
			# state.acq.pixelTime = 3.2e-06
			if line.find('state.acq.pixelTime') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.dwellTime = float(rhs)

			# state.motor.absXPosition = -9894.4
			if line.find('state.motor.absXPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motorx = float(rhs)

			# state.motor.absYPosition = -18423.4
			if line.find('state.motor.absYPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motory = float(rhs)

			# state.motor.absZPosition = -23615.04
			if line.find('state.motor.absZPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motorz = float(rhs)

			# state.acq.zStepSize = 2
			if line.find('state.acq.zStepSize') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.voxelz = float(rhs)

			# state.internal.triggerTimeString = '10/2/2014 12:29:22.796'
			if line.find('state.internal.triggerTimeString') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace("'","")
				if rhs.startswith(' '): # if date string starts with space, remove it
					rhs = rhs[1:-1]
				datetime = rhs.split(' ')
				# 20170811, there is an extra fucking space before datestr on the rhs
				# convert mm/dd/yyyy to yyyymmdd
				#print 'rhs:' + "'" + rhs + "'"
				#print 'datetime:', datetime
				self.dateStr = bFixDate(datetime[0], logLevel)
				self.timeStr = bFixTime(datetime[1], logLevel)
				

			# state.acq.acqDelay = 0.000122
			# state.acq.bidirectionalScan = 0
			# state.acq.fillFraction = 0.706206896551724
			# state.acq.frameRate = 0.841864224137931
			# huganir lab keeps this off, image pixel intensities are 2^11 * samplesperpixel (e.g. binFactor?)
			# state.acq.binFactor = 16
			# state.internal.averageSamples = 1
			# the real image bit depth is usually inputBitDepth-1 (1 bit is not used?)
			# state.acq.inputBitDepth = 12

		if scanImageVersion and foundZoom:
			self.voxelx = magic_scan_image_scale / self.zoom * (1024 / self.width)
			self.voxely = magic_scan_image_scale / self.zoom * (1024 / self.height)
		else:
			bPrintLog('ERROR: Did not find zoom in SI header, voxel x/y will be wrong', logLevel)
			
	###################################################################################
	def readZeissHeader(self, infoStr):		
		# This is incredibly difficult to get working as (date, time, voxels) are in different obscure places in lsm and czi
		# Furthermore, just trying to read the raw ome xls is futile
		#
		# parsing ome xml as a string and searching it with regular expression(re) does not work
		# it is beyond the scope of my work to figure this out
		# the fact that it does not work and there is little documentaiton is a pretty big waste of time
		#
		# get and parse xml to find date/time
		#fi = self.imp.getOriginalFileInfo(); # returns a FileInfo object
		#omexml = fi.description #omexml is a string
		#omexml = omexml.encode('utf-8')
		#omexml = omexml.replaceAll("[^\\x20-\\x7e]", "") # see: https://stackoverflow.com/questions/2599919/java-parsing-xml-document-gives-content-not-allowed-in-prolog-error

		# (1) try and search the ome xml like a string, this gives errors
		#docsPattern = '<AcquisitionDate>.*</AcquisitionDate>'
		#searchresult = re.search(docsPattern, omexml)
		#print 'searchresult:', searchresult.group(0)
		
		# 2) treat the ome xml like any other xml (because it's xml, right?)
		# well this raises errors too
		#omexml has <AcquisitionDate>2016-08-17T15:21:50</AcquisitionDate>
		#import xml.etree.ElementTree
		#e = xml.etree.ElementTree.fromstring(omexml).getroot()		#print omexml
		#for atype in e.findall('AcquisitionDate'):
		#	print 'AcquisitionDate:', atype #.get('foobar')
		#
		#

		if self.islsm:
			# lsm have date hidden in omeMeta.getImageAcquisitionDate(0)
			# this is copied from code at: https://gist.github.com/ctrueden/6282856
			reader = ImageReader()
			omeMeta = MetadataTools.createOMEXMLMetadata() #omeMeta.getImageAcquisitionDate(0)
			reader.setMetadataStore(omeMeta)
			reader.setId(self.filepath)
			#seriesCount = reader.getSeriesCount()
			dateTimeStr = omeMeta.getImageAcquisitionDate(0) #2016-08-17T16:36:26
			reader.close()
			if dateTimeStr:
				self.dateStr, self.timeStr = dateTimeStr.toString().split('T')
				self.dateStr = bFixDate(self.dateStr)
				self.timeStr = bFixTime(self.timeStr)
				#bPrintLog('LSM date/time is: ' + self.dateStr + ' ' + self.timeStr, 3)
			else:
				bPrintLog('WARNING: did not get Zeiss date/time string')

			# lsm have voxels in infoStr
			for line in infoStr.split('\n'):
				#print line
				if line.find('VoxelSizeX') != -1:
					self.voxelx = float(line.split('=')[1])
				if line.find('VoxelSizeY') != -1:
					self.voxely = float(line.split('=')[1])
				if line.find('VoxelSizeZ') != -1:
					self.voxelz = float(line.split('=')[1])
				if line.find('SizeC') != -1:
					self.numChannels = int(line.split('=')[1])
				#if line.find('BitsPerPixel') and not line.startswith('Experiment') != -1: # 20170811, startswith is for czi
				#	self.bitsPerPixel = int(line.split('=')[1])
				if line.find('RecordingZoomX#1') != -1:
					self.zoom = int(line.split('=')[1])

		if self.isczi:
			# czi has date/time in infoStr (lsm does not)
			for line in infoStr.split('\n'):
				if line.find('CreationDate #1') != -1: # w.t.f. is #1 referring to?
					lhs, rhs = line.split('=')
					rhs = rhs.replace('	', ' ')
					if rhs.startswith(' '):
						rhs = rhs[1:-1]
					#print "lhs: '" + lhs + "'" + "rhs: '" + rhs + "'"
					if rhs.find('T') != -1:
						self.dateStr, self.timeStr = rhs.split('T')
					else:
						self.dateStr, self.timeStr = rhs.split(' ')
					self.dateStr = bFixDate(self.dateStr)
					self.timeStr = bFixTime(self.timeStr)
					#bPrintLog('CZI date/time is: ' + self.dateStr + ' ' + self.timeStr, 3)
				# .czi
				# <Pixels BigEndian="false" DimensionOrder="XYCZT" ID="Pixels:0" Interleaved="false" PhysicalSizeX="0.20756645602494875" PhysicalSizeXUnit="µm" PhysicalSizeY="0.20756645602494875" PhysicalSizeYUnit="µm" PhysicalSizeZ="0.75" PhysicalSizeZUnit="µm" SignificantBits="8" SizeC="1" SizeT="1" SizeX="1024" SizeY="1024" SizeZ="50" Type="uint8">

			# czi have voxel in calibration
			self.voxelx = self.imp.getCalibration().pixelWidth; 
			self.voxely = self.imp.getCalibration().pixelHeight; 
			self.voxelz = self.imp.getCalibration().pixelDepth; 
			#bPrintLog('readZeissHeader() read czi scale as: ' + str(self.voxelx) + ' ' + str(self.voxely) + ' ' + str(self.voxelz), 3)

			# CLEARING self.infoStr for CZI ... it was WAY to big to parse in Map Manager
			self.infoStr = ''
			
	###################################################################################
	def printParams(self, loglevel=3): # careful, thefunction print() is already taken?
		bPrintLog('file:' + self.filepath, loglevel)
		bPrintLog("date:'" + self.dateStr + "' time:'" + self.timeStr + "'", loglevel)
		bPrintLog('channels:' + str(self.numChannels), loglevel)
		bPrintLog('zoom:' + str(self.zoom), loglevel)
		bPrintLog('bitDepth:' + str(self.bitDepth), loglevel)
		bPrintLog('pixels:' + str(self.width) + ',' + str(self.height)+ ',slices ' + str(self.numSlices) + ',frames ' + str(self.numFrames), loglevel)
		bPrintLog('voxels:' + str(self.voxelx) + ',' + str(self.voxely)+ ',' + str(self.voxelz), loglevel)

	###################################################################################
	def deinterleave(self):
		if self.numChannels == 1:
			bPrintLog('Warning: deinterleave() did not deinterleave with num channels 1', 0)
			return -1
		
		#IJ.run('Deinterleave', 'how=' + str(self.numChannels) +' keep') #makes ' #1' and ' #2', with ' #2' frontmost
		cmdStr = 'how=' + str(self.numChannels) + ' keep'
		IJ.run('Deinterleave', cmdStr) #makes ' #1' and ' #2', with ' #2' frontmost
		for i in range(self.numChannels):
			currenChannel = i + 1
			currentWindowName = self.windowname + ' #' + str(currenChannel)
			self.channelWindows.append(currentWindowName)
			
			currentImp = WindowManager.getImage(currentWindowName)
			if currentImp:
				self.channelImp.append(currentImp)
			else:
				bPrintLog('ERROR: deinterleave() did not find window names:' + currentWindowName, 0)
			
	###################################################################################
	# added 20190302 davis
	def convertTo8Bit(self):
		# turn off convert to 8-bit if image is already 8-bit
		# e a requering channel 1, assum eother channels are the same
		
		#impBitDepth = self.imp_ch1.getBitDepth()
		#if impBitDepth == 8:
		#	return 1

		# setDoScaling(True) will scale max intensity down to 255
		# setDoScaling(False) will take bt depth of original (usually 16-bit) and scale max (2^16-1) down to 255
		mySetDoScaling = True
		ImageConverter.setDoScaling(mySetDoScaling)
		
		# run("8-bit");
		bPrintLog('converting to 8-bit with setDoScaling ' + str(mySetDoScaling), 3)
		
		'''
		if self.imp_ch1:
			if self.imp_ch1.getBitDepth() != 8:
				IJ.run(self.imp_ch1, "8-bit", ''); #does this in place, no new window
		if self.imp_ch2:
			if self.imp_ch2.getBitDepth() != 8:
				IJ.run(self.imp_ch2, "8-bit", ''); #does this in place, no new window
		if self.imp_ch3:
			if self.imp_ch3.getBitDepth() != 8:
				IJ.run(self.imp_ch3, "8-bit", ''); #does this in place, no new window
		'''
		
		for imp in self.channelImp:
			if imp.getBitDepth() != 8:
				IJ.run(imp, "8-bit", ''); #does this in place, no new window

	###################################################################################
	def exportTifStack(self, destFolder=''):
		channelNumber = 1
		for imp in self.channelImp:
			if not destFolder:
				destFolder = os.path.join(self.enclosingPath, self.enclosingfolder + '_tif')
			if not os.path.isdir(destFolder):
				os.makedirs(destFolder)
			
			if not imp:
				bPrintLog("ERROR: exportTifStack() did not find an imp at channel number '" + str(channelNumber) + "'", 0)
				return -1
				
			self.updateInfoStr()
			imp.setProperty("Info", self.infoStr);

			saveFile = os.path.splitext(self.filename)[0] + '_ch' + str(channelNumber) + '.tif'
			savePath = os.path.join(destFolder, saveFile)

			# save
			fs = FileSaver(imp)
			bPrintLog('saveTifStack():' + savePath, 3)
			if imp.getNSlices()>1:
				fs.saveAsTiffStack(savePath)
			else:
				fs.saveAsTiff(savePath)

			channelNumber += 1

	###################################################################################
	def saveMaxProject(self, destFolder=''):
		channelNumber = 1
		for imp in self.channelImp:
			if not destFolder:
				destFolder = os.path.join(self.enclosingPath, self.enclosingfolder + '_tif', 'max')
			if not os.path.isdir(destFolder):
				os.makedirs(destFolder)

			# make max project
			if gSaveSingleImage:
				imp.setSlice(1)
				ip = imp.getProcessor()
				zimp = ImagePlus('zimp', ip)
			else:
				zp = ZProjector(imp)
				zp.setMethod(ZProjector.MAX_METHOD)
				zp.doProjection()
				zimp = zp.getProjection()

			# save
			saveFile = 'max_' + os.path.splitext(self.filename)[0] + '_ch' + str(channelNumber) + '.tif'
			savePath = os.path.join(destFolder, saveFile)
			fs = FileSaver(zimp)
			bPrintLog('saveMaxProject():' + savePath, 3)
			fs.saveAsTiff(savePath)

			channelNumber += 1
			
	###################################################################################
	def closeAll(self):
		self.imp.changes = False
		self.imp.close()
		for imp in self.channelImp:
			imp.close()
			
##################################################################################################
def runOneFile(filepath):
	"""
	Convert one file.
	Return detection parameters in a dictionary
	"""
	if not os.path.isfile(filepath):
		bPrintLog('ERROR: runOneFile() did not find file: ' + filepath,0)
		return 0

	bPrintLog('runOneFile() filepath:' + filepath, 2)
	theImage = bImp(filepath)
	theImage.printParams()

	# added 20190302 davis
	if gConvertTo8Bit:
		theImage.convertTo8Bit()
	
	if gSaveImages:
		ok = theImage.exportTifStack()
		if ok == -1:
			bPrintLog('ERROR: runOneFile() was not able to export stack:' + filepath, 0)
		theImage.saveMaxProject()
	
	# added 20190302 davis
	detectDict = theImage.saveHeaderFile()
	
	theImage.closeAll()

	return detectDict
	
##################################################################################################
def runOneFolder(sourceFolder):
	if not os.path.isdir(sourceFolder):
		bPrintLog('ERROR: runOneFolder() did not find folder: ' + sourceFolder)
		return 0

	bPrintLog('runOneFolder() sourceFolder:' + sourceFolder, 1)

	acceptedExtensions = ['.czi', '.lsm', '.tif', '.nd2', '.oir']

	# count number of lsm files
	numLSM = 0
	for filename in os.listdir(sourceFolder):
		baseName, extension = os.path.splitext(filename)
		#if filename.endswith(".lsm"):
		if not filename.startswith('.') and extension in acceptedExtensions:
			numLSM += 1
				
	detectList = [] # accumulate a detection dict for each converted file
	
	#fileList = []
	outLSM = 1
	for filename in os.listdir(sourceFolder):		
		baseName, extension = os.path.splitext(filename)
		
		#islsm = filename.endswith(".lsm")
		#istif = filename.endswith(".tif")
		#if outLSM==1 or outLSM==2: # to run one file for debugging
		#if 1:
		#if filename.endswith(".lsm"):
		if extension in acceptedExtensions:
			#if islsm or istif:
			#fileList.append(filename)
			filePath = sourceFolder + filename
			bPrintLog(str(outLSM) + ' of ' + str(numLSM), 2)
			#
			detectDict = runOneFile(filePath)
			detectList.append(detectDict)
			#
			outLSM += 1

	#
	# write detection parameters for all converted files into one .csv file
	if len(detectList) > 0:
		if sourceFolder.endswith('/'):
			sourceFolder = sourceFolder[:-1]
		grandparentPath, parentFolder = os.path.split(sourceFolder)
		dstTextFile = os.path.join(sourceFolder, parentFolder + '.csv')
		bPrintLog('Saving: ' + dstTextFile, 2)
		with open(dstTextFile, 'w') as f:
			for idx, fileDict in enumerate(detectList):
				if idx == 0:
					# write header
					for k in fileDict.keys():
						f.write(k + ',')
					f.write('\n')
				for k,v in fileDict.items():
					f.write(str(v) + ',')
				f.write('\n')
				
	return outLSM
	
##################################################################################################
# utility
##################################################################################################
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '	'
		print '	 ',
	print text #to command line
	IJ.log(msgStr + text)

##################################################################################################
def bFixTime(timestr, logLevel=0):
	
	# remove fractonal seconds (This ASSUMES the only place we would find a '.' is after seconds !!!)
	dotIdx = timestr.find('.')
	if dotIdx > 0:
		timestr = timestr[0:dotIdx-1]

	hh, mm, ss = timestr.split(':')
	
	# zero pad hh:mm:ss
	hh = hh.zfill(2)
	mm = mm.zfill(2)
	ss = hh.zfill(2)
	
	timestr = hh + ":" + mm + ":" + ss
	return timestr
##################################################################################################
def bFixDate(datestr, logLevel=0):
	# try and return datStr as yyyymmdd

	# determine if date is delimited with ('/', '-', '_')
	if datestr.find('/') != -1:
		datedelim = '/'
	elif datestr.find('-') != -1:
		datedelim = '-'
	elif datestr.find('_') != -1:
		datedelim = '_'
	else:
		datedelim = None
		bPrintLog('ERROR: did not recognize date:' + datestr + '. Expecting (/, -, _)', logLevel)
	
	# parse date depending on user specified global date_order
	if date_order == 'mmddyyyy':
		if datedelim:
			mm, dd, yyyy = datestr.split(datedelim)
		else:
			mm = datestr[0:1]
			dd = datestr[2:3]
			yyyy = datestr[4:7]
	elif date_order == 'ddmmyyyy':
		if datedelim:
			dd, mm, yyyy = datestr.split(datedelim)
		else:
			mm = datestr[0:1]
			dd = datestr[2:3]
			yyyy = datestr[4:7]
	elif date_order == 'yyyymmdd':
		if datedelim:
			yyyy, mm, dd = datestr.split(datedelim)
		else:
			yyyy = datestr[0:3]
			mm = datestr[4:5]
			dd = datestr[6:7]
	else:
		bPrintLog('ERROR: bFixDate() did not recognize date_order:' + date_order, logLevel)

	#zero pad mm, dd, and yyyy
	mm = mm.zfill(2)
	dd = dd.zfill(2)
	if len(yyyy) != 4:
		bPrintLog('ERROR: Y2K bug, your year should be 4 characters long, got year:' + yyyy, logLevel)
	retStr = yyyy + mm + dd
	return retStr


##################################################################################################
# main
##################################################################################################
"""
	print __name__
	__name__ is	'__builtin__' in Fiji downloaded on 20170810.
"""
if __name__ in ['__main__', '__builtin__']: 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bFolder2MapManager')
	bPrintLog('*** IMPORTANT *** Using magic_scan_image_scale:' + str(magic_scan_image_scale) + ' for ScanImage files. voxel (um) = ' + str(magic_scan_image_scale) + '/zoom')
	
	#sourceFolder = '/Volumes/fourt/MapManager_Data/sarah_immuno/8.17.16/8.17.16.mdb/'
	sourceFolder = DirectoryChooser("Please Choose A Directory Of Files").getDirectory()

	outFiles = 0
	if (sourceFolder):
		outFiles = runOneFolder(sourceFolder)
	else:
		bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	bPrintLog('Finished bFolder2MapManager with ' + str(outFiles) + ' files in ' + str(round(stopTime-startTime,2)) + ' seconds')
	bPrintLog('=================\n')
	