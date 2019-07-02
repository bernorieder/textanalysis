# https://www.learnpyqt.com/courses/packaging-and-distribution/packaging-pyqt5-apps-fbs/

# solved NLTK freeze issues with: https://stackoverflow.com/questions/54659466/nltk-hook-unable-to-find-nltk-data

#from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2 import QtCore, QtWidgets, QtGui
 
import sys
import random
import re
import operator

import emoji
import nltk
from nltk.collocations import *
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.construct_ui()

	# method sets up the user interface
	def construct_ui(self):
		self.setWindowTitle('TextAnalysis')

		self.mainWidget = QtWidgets.QWidget()
		self.setCentralWidget(self.mainWidget)

		self.statusBar = QtWidgets.QStatusBar()
		self.setStatusBar(self.statusBar)

		layout = QtWidgets.QGridLayout()
		self.mainWidget.setLayout(layout)

		# text input
		layout.addWidget(QtWidgets.QLabel("Paste text to analyze or "),0, 0, 1, 2)
		self.button_file = QtWidgets.QPushButton("open file")
		
		layout.addWidget(self.button_file,0, 2, 1, 1)
		self.textin = QtWidgets.QPlainTextEdit("👍 and 📋 and 👌 and 😋 and 👍 again. In an interview on BBC Radio 4’s Today programme, Raab argued that leaving the EU without a deal would not be a problem, partly because the general agreement on tariffs and trade (Gatt) could be applied to create a standstill on tariffs with the EU. Mark Carney, the governor of the Bank of England, and Liam Fox, the trade secretary, have said it is not possible for the UK to trigger this unilaterally. But Raab said Carney was not a lawyer and claimed that legally it could be done and the question is whether there is the political will.")
		layout.addWidget(self.textin,1, 0, 1, 4)

		self.separatorLine1 = QtWidgets.QFrame()
		self.separatorLine1.setFrameShape(QtWidgets.QFrame.HLine)
		self.separatorLine1.setFrameShadow(QtWidgets.QFrame.Plain)
		self.separatorLine1.setLineWidth(1)
		layout.addWidget(self.separatorLine1, 2, 0, 1, 4)

		# emoji interface
		layout.addWidget(QtWidgets.QLabel("Create emoji statistics:"),3, 0, 1, 4)
		self.button_emoji = QtWidgets.QPushButton("analyze")
		layout.addWidget(self.button_emoji,4, 0, 1, 1)
		self.textout_emoji = QtWidgets.QPlainTextEdit()
		self.textout_emoji.setPlainText("output goes here (copy and paste into e.g. a spreadsheet)")
		layout.addWidget(self.textout_emoji,5, 0, 1, 4)
		
		self.separatorLine2 = QtWidgets.QFrame()
		self.separatorLine2.setFrameShape(QtWidgets.QFrame.HLine)
		self.separatorLine2.setFrameShadow(QtWidgets.QFrame.Plain)
		self.separatorLine2.setLineWidth(1)
		layout.addWidget(self.separatorLine2, 6, 0, 1, 4)

		# bigram interface
		layout.addWidget(QtWidgets.QLabel("Create ngram statistics:"),7, 0, 1, 4)
		layout.addWidget(QtWidgets.QLabel("Stopwords:"),8, 0, 1, 1)
		self.languagelist = QtWidgets.QComboBox()
		self.languagelist.addItem("- none -")
		for item in stopwords.fileids():
			self.languagelist.addItem(item)
		layout.addWidget(self.languagelist,8, 1, 1, 1)
		layout.addWidget(QtWidgets.QLabel("Windowsize:"),8, 2, 1, 1)
		self.windowsize = QtWidgets.QLineEdit()
		self.windowsize.setMaxLength(1)
		self.windowsize.setText("2")
		layout.addWidget(self.windowsize,8, 3, 1, 1)
		self.button_ngrams = QtWidgets.QPushButton("analyze")
		layout.addWidget(self.button_ngrams,9, 0, 1, 1)
		self.textout_ngrams = QtWidgets.QPlainTextEdit()
		self.textout_ngrams.setPlainText("output goes here (copy and paste into e.g. a spreadsheet)")
		layout.addWidget(self.textout_ngrams,10, 0, 1, 4)

		# event binding
		self.button_file.clicked.connect(self.opentextfile)
		self.button_emoji.clicked.connect(self.emojistats)
		self.button_ngrams.clicked.connect(self.start_ngrams)
		
	def opentextfile(self):

		filepath = QtWidgets.QFileDialog.getOpenFileName(self,"Open Image",".", "Text Files (*.txt)")[0];

		self.statusBar.showMessage("loaded file: " + filepath)
		self.statusBar.repaint()

		with open(filepath) as f:
			textdata = f.read()

		self.textin.setPlainText(textdata)
		self.textin.repaint()


	def savecsvfile(self):
		print("ho")

	# method creates emoji stats
	def emojistats(self):

		content = self.textin.toPlainText()

		search = re.findall(r"::([\w_]+)::",emoji.demojize(content,delimiters=(" ::",":: ")))

		emojis = {}
		for item in search:
			convert = emoji.emojize(item, use_aliases=True, delimiters=("::","::"))
			if convert not in emojis:
				emojis[convert] = 1
			else:
				emojis[convert] += 1

		if len(emojis.items()) > 0:
			output = "emoji,alias,frequency\n"
			for item in sorted(emojis.items(), key=operator.itemgetter(1), reverse=True):
				output += item[0] + "," + emoji.emojize(":"+item[0]+":", use_aliases=True)  + "," + str(item[1]) + "\n"
		else:
			output = "no emojis found"

		self.textout_emoji.setPlainText(output)
		self.textout_emoji.repaint()

	# method calls the ngram thread
	def start_ngrams(self):
		
		self.statusBar.showMessage("processing...")
		self.statusBar.repaint()

		params = {}
		params["content"] = self.textin.toPlainText()
		params["windowsize"] = int(self.windowsize.text())
		params["language"] = self.languagelist.currentText()
		
		self.thread = NgramsThread(params=params)
		self.thread.results.connect(self.done_ngrams)
		self.thread.start()

	# method called when ngram processing is finished
	@QtCore.Slot(object)
	def done_ngrams(self,output):
		self.textout_ngrams.setPlainText(output)
		self.textout_ngrams.repaint()
		self.statusBar.clearMessage()
		self.statusBar.repaint()


# this class handles the processing of ngrams via NLTK in a separate thread
class NgramsThread(QtCore.QThread):
	
	results = QtCore.Signal(object)

	def __init__(self, params):
		QtCore.QThread.__init__(self)
		self.params = params

	def run(self):

		bigram_measures = nltk.collocations.BigramAssocMeasures()

		content = self.params["content"].lower()

		regex = re.compile("[^a-zA-Z0-9 ]")
		content = regex.sub(" ",content)

		tokenizer = RegexpTokenizer(r"\w+")
		tmptokens = tokenizer.tokenize(content)

		if self.params["language"] != "- none -":
			mystopwords = stopwords.words(self.params["language"])
			tokens = []
			for word in tmptokens:
				if word not in mystopwords:
					tokens.append(word)
		else:
			tokens = tmptokens


		if len(finder.ngram_fd.items()) > 0:
			output = "bigram,frequency\n"
			for item in sorted(finder.ngram_fd.items(), key=operator.itemgetter(1), reverse=True):
				output += item[0][0] + " " + item[0][1] + "," + str(item[1]) + "\n"
		else:
			output = "no bigrams generated"

		self.results.emit(output)



if __name__ == "__main__":
	
	app = QtWidgets.QApplication(sys.argv)
	w = MainWindow()
	w.setObjectName("MainWindow")
	w.resize(640, 480)
	w.show()

	sys.exit(app.exec_())