import sys
import re
import requests
from timeit import default_timer
import logging
import threading

from PyQt5.QtWidgets import QMenu, QAction, QGridLayout, QVBoxLayout, QDesktopWidget, QTreeView, QAbstractItemView, QHeaderView, QStackedWidget, QHBoxLayout, QListWidget, QFileDialog,QProgressBar, QCheckBox, QComboBox, QPushButton, QLabel, QTabWidget, QWidget, QMainWindow, QLineEdit, QMessageBox, QApplication, QStackedWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QWaitCondition, QMutex, Qt, QUrl
from PyQt5.QtGui import  QStandardItemModel, QStandardItem, QMouseEvent
from PyQt5.QtWebEngineWidgets import QWebEngineView


#from core import run_medium
#from core2 import run_twit
import xlrd
import xlwt

from datetime import datetime, timedelta




class ListView(QTreeView):
    def __init__(self, *args, **kwargs):
        super(ListView, self).__init__(*args, **kwargs)
        self.setModel(QStandardItemModel(self))
        self.model().setColumnCount(2)
        self.setRootIsDecorated(False)
        self.setAllColumnsShowFocus(True)
        self.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)



    def addItem(self, key, value):
        first = QStandardItem(key)
        second = QStandardItem(value)
        second.setTextAlignment(Qt.AlignRight)
        self.model().appendRow([first, second])

    def openMenu(self, position):

        indexes = self.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        menu = QMenu()
        self.delete = menu.addAction(self.tr("xóa"))
        self.delete.triggered.connect(self.onDel)

        menu.exec_(self.viewport().mapToGlobal(position))

    def onDel(self,item):
        try:
            f = open("delete.txt","a")
        except(FileNotFoundError):
            f = open("delete.txt","w")
        f.write(self.selectedIndexes()[0].data(Qt.DisplayRole)+"\n")
        f.close()
        self.model().removeRow(self.selectedIndexes()[0].row())



    def remove(self,pos):
        self.model().removeRow(pos)

    def removeAll(self):
        print("rows {0}".format(self.model().rowCount()))
        for i in range(0,self.model().rowCount()+1):
            self.model().removeRow(i)



class ProgressThread(QThread):

    taskFinished = pyqtSignal()
    labelCon = pyqtSignal(str)
    labelPause = pyqtSignal(str)
    proceeded = pyqtSignal(list)
    deleted = pyqtSignal(int)
    saved = pyqtSignal(list)

    @pyqtSlot()
    def __init__(self,users,keyword,parent=None):
        QThread.__init__(self,parent)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.cnt = 0
        self._status = True
        self.users = users
        self.keyword = keyword
        self.lst_url = []
        self.row_lst = []
        self.del_lst = []
        self.x = []
        self.cur_pair = []
        self.length = 0
        self.count = 0
        self.thread_num = 50
        self.last_time = datetime.now()
        self.cur_time = datetime.now()
        self.delta = self.last_time

    def __del__(self):
        self.wait()


    def make_requests(self,this_str, keyword,START_TIME):
        if("twitter.com" in this_str):
            print(this_str)
            self.x = run_twit(this_str,keyword)
            self.length += len(self.x)
            print(len(self.x))
            self.x = [pair for pair in self.x if(pair[0]+"\n" not in self.del_lst)]
            self.lst_url.append(self.x)
            self.proceeded.emit(self.x)
            print("done")
        elif("medium.com" in this_str):
            self.x = run_medium(this_str,keyword)
            self.length += len(self.x)
            print(len(self.x))
            self.x = [pair for pair in self.x if(pair[0]+"\n" not in self.del_lst)]
            self.lst_url.append(self.x)
            self.proceeded.emit(self.x)
            print("done")
        self.saved.emit(self.lst_url)


        elapsed = default_timer() - START_TIME
        time_completed_at = "{:5.2f}s".format(elapsed)
        print(time_completed_at)

    def multi_req(self,sheet,row,START_TIME):
        if not self._status:
            self.cond.wait(self.mutex)
        this_str = sheet.cell_value(row,0)
        if(this_str == ""):
            pass
        else:
            threads = [
                threading.Thread(
                    target=self.make_requests,
                        args=(this_str,keyword,START_TIME)
                            ) for keyword in self.keyword
                    ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    def run(self):
        START_TIME = default_timer()
        while(True):
            try:
                with open('delete.txt') as del_urls:
                    for url in del_urls:
                        self.del_lst.append(url)
                        print(self.del_lst)
            except(FileNotFoundError):
                f = open("delete.txt","w")
                f.close()
            # this can pause and resume thread
            book = xlrd.open_workbook(self.users)
            sheet = book.sheet_by_index(0)
            self.mutex.lock()
            current_row = sheet.nrows

            for row in range(0,sheet.nrows):
                print(current_row-1)
                print(row)
                if(len(self.row_lst)<self.thread_num and  (row != current_row-1)):
                    self.row_lst.append(row)
                    if(row == current_row-2):
                        self.row_lst.append(current_row-1)
                else:
                    print("begin")
                    print(self.row_lst)
                    threads = [
                        threading.Thread(
                            target=self.multi_req,
                                args=(sheet,element,START_TIME)
                                    ) for element in self.row_lst
                            ]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join()
                    print(self.row_lst)
                    self.row_lst = []
                    self.row_lst.append(row)
                    print(len(self.row_lst))
                    print(row)




                        #self.proceeded.emit(self.x) # there is duplication if emit outside
            print("\n\n")
            print("its here")
            print(self.lst_url)
            self.last_time = datetime.now()
            self.delta = self.last_time + timedelta(minutes = 0,hours = 5)
            print("The last time: ")
            print(self.last_time)
            print("The delta: ")
            print(self.delta)
            self.del_lst = []
            self.row_lst = []
            self.count = 0
            self.mutex.unlock()
            self.labelPause.emit("Đã quét xong")
            while(True):
                self.cur_time = datetime.now()
                if(self.cur_time > self.delta):
                    self.last_time = datetime.now()
                    self.deleted.emit(self.length)
                    self.labelCon.emit("Đang lấy dữ liệu")
                    print(self.length)
                    self.lst_url =[]
                    self.length = 0
                    break
                else:
                    pass


        self.taskFinished.emit()


    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status



# For loading data
class Progress(QWidget):
    switch_to_gui = pyqtSignal(list)
    displayed = pyqtSignal(list)


    def __init__(self,users,keyword,parent=None):
        QWidget.__init__(self,parent,flags = Qt.Widget)
        self.users = users
        self.keyword = keyword
        self.lst_url = []
        self.row = 0
        self.state = False


    def initUi(self):
        # Create a progress bar and a button and add them to the main layout
        self.layout = QVBoxLayout(self)
        self.lst = ListView()
        #self.web = QWebEngineView()
        self.myLongTask = ProgressThread(self.users,self.keyword,self)
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0,1)
        self.layout.addWidget(self.lst)
        #self.layout.addWidget(self.web)
        self.layout.addWidget(self.progressBar)
        self.label = QLabel("",self)
        self.btn = QPushButton("Dừng")
        self.save_btn = QPushButton("Xuất")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn)
        self.layout.addWidget(self.save_btn)
        self.btn.clicked.connect(self.onPressed)
        self.save_btn.clicked.connect(self.onSave)
        self.myLongTask.saved.connect(self.onWrite)
        self.myLongTask.labelCon.connect(self.lbCon)
        self.myLongTask.labelPause.connect(self.lbPause)
        self.lst.clicked.connect(self.Clicked)
        self.myLongTask.deleted.connect(self.onDel)


        self.loadThread()

    def onPressed(self):
        self.myLongTask.toggle_status()
        self.btn.setText({True: "Dừng", False: "Tiếp tục"}[self.myLongTask.status])

    def onSave(self):
        self.state = True
        print("we will be here")

    @pyqtSlot(str)
    def lbCon(self,text):
        self.label.setText(text)
    @pyqtSlot(str)
    def lbPause(self,text):
        self.label.setText(text)

    @pyqtSlot(list)
    def onWrite(self,items):
        if(self.state):
            self.myLongTask.status = False
            self.myLongTask.toggle_status()
            book= xlwt.Workbook()
            sheet = book.add_sheet('Sheet 1')
            sheet.write(0, 0, 'url')
            sheet.write(0,1,'keyword')
            print(items)
            for item in items:
                for pair in item:
                    self.row +=1
                    sheet.write(self.row, 0, pair[0])
                    sheet.write(self.row,1,pair[1])
            print("it's done")
            self.row = 0
            book.save('data.xls')
            self.myLongTask.status = True
            self.state = False

    def Clicked(self):
        item = self.lst.selectedIndexes()[0]
        #get keywords
        item1 = self.lst.selectedIndexes()[1]
        print(item1.data(Qt.DisplayRole))
        print(item)
        self.displayed.emit([item.data(Qt.DisplayRole),item1.data(Qt.DisplayRole)])

    @pyqtSlot(int)
    def onDel(self,len_lst):
        for i in range(0,len_lst):
            print("delete")
            self.lst.remove(False)

    def loadThread(self):
        self.progressBar.setRange(0,0)
        self.label.setText("Đang lấy dữ liệu")
        self.myLongTask.start()
        self.myLongTask.proceeded.connect(self.onProceeded)
        self.myLongTask.taskFinished.connect(self.onFinished)

    @pyqtSlot(list)
    def onProceeded(self,pairs):
        print("pair is here: {0}".format(pairs))
        for pair in pairs:
            if(len(pair)>0):
                self.lst.addItem(pair[0],pair[1])




    def onFinished(self):
        # Stop the pulsation
        self.progressBar.setRange(0,1)
        self.lst_url = self.myLongTask.lst_url
        print("its here 2")
        print(self.lst_url)
        self.switch_to_gui.emit(self.lst_url)

# For display
class login_ui(QWidget):
    check_pass = pyqtSignal(list)
    def __init__(self,parent):
        super(login_ui,self).__init__()
        self.usr = QLineEdit(self)
        self.usr.move(120,100)
        self.usr.setPlaceholderText("Điền user")
        self.usr_lb = QLabel("user",self)
        self.usr_lb.move(5,100)
        self.passw = QLineEdit(self)
        self.passw.setEchoMode(QLineEdit.Password)
        self.passw.setPlaceholderText("Điền pass")
        self.passw.move(120,130)
        self.pass_lb = QLabel("password",self)
        self.pass_lb.move(5,130)
        self.btn = QPushButton("Đăng nhập",self)
        self.btn.move(150,230)
        self.btn.clicked.connect(self.onClicked)

    def onClicked(self):
        print([self.usr.text(),self.passw.text()])
        self.check_pass.emit([self.usr.text(),self.passw.text()])

class load_ui(QWidget):
    trans = pyqtSignal(list)


    def __init__(self,parent):
        super(load_ui,self).__init__()
        self.vLayout = QVBoxLayout(self)
        self.lst = []
        self.lstKey = []

        self.selFile = QLineEdit(self)
        self.lst_usr = QListWidget(self)
        self.selFileBtn = QPushButton("IMPORT",self)
        self.selFileBtn.clicked.connect(self.selectFile)
        self.key = QLineEdit(self)
        self.key.setPlaceholderText("Điền keywords, ngăn cách bởi dấu phẩy")


        self.btn = QPushButton("Quét",self)
        self.vLayout.addWidget(self.selFile)
        self.vLayout.addWidget(self.selFileBtn)
        self.vLayout.addWidget(self.lst_usr)
        self.vLayout.addWidget(self.key)
        self.vLayout.addWidget(self.btn)
        self.setLayout(self.vLayout)
        self.selFileBtn.clicked.connect(self.display)
        self.btn.clicked.connect(self.onClicked)


    def check(self):
        if(self.selFile.text()[-4:] != ".xls"):
            if(self.selFile.text()[-5:] != ".xlsx"):
                QMessageBox.warning(self,"Cảnh báo","Hãy chọn file users")
                return False
        else:
            return True

    def display(self):
        # clear all items of previous list
        self.lst_usr.clear()
        check = self.check()
        if(check):
            book = xlrd.open_workbook(self.selFile.text())
            sheet = book.sheet_by_index(0)
            for row in range(0,sheet.nrows):
                item = sheet.cell_value(row,0)
                self.lst_usr.addItem(item)

    def onClicked(self):
        check = self.check()
        if (check):

            self.lstKey = self.key.text().split(',')
            self.lst.append(self.selFile.text())
            self.lst.append(self.lstKey)
            self.trans.emit(self.lst)
            self.lst = []

    def selectFile(self):
        self.selFile.setText(QFileDialog.getOpenFileName()[0])






# --------------- Main UI -----------------

class main_ui(QWidget):
    def __init__(self,parent):
        super(main_ui,self).__init__()
        self.grid = QGridLayout(self)
        self.ui = load_ui(self)
        self.lst_url = ListView()
        self.web = QWebEngineView()
        self.current_widget = QStackedWidget(self)
        self.current_widget.addWidget(self.lst_url)
        self.current_widget.setCurrentWidget(self.lst_url)
        self.grid.addWidget(self.ui,0,0)
        self.grid.addWidget(self.current_widget,0,1)
        self.grid.addWidget(self.web,0,2)
        self.setLayout(self.grid)

class main_window(QMainWindow):
    def __init__(self):
        super(main_window,self).__init__()
        self.lst = []
        self.result = ''
        self.keyword = ''
        self.result_match = ''
        self.widget = QStackedWidget(self)
        self.login = login_ui(self)
        self.main = main_ui(self)
        self.widget.addWidget(self.login)
        self.widget.setCurrentWidget(self.login)
        self.main.ui.trans.connect(self.onSwitched)
        self.screen = QDesktopWidget().screenGeometry()
        x_loc = int((self.screen.width() - 450) / 2)
        y_loc = int((self.screen.height() - 300) / 2)
        self.setGeometry(x_loc, y_loc, 450, 300)

        self.login.check_pass.connect(self.switch_to_main)
        self.setCentralWidget(self.widget)
        self.show()

    @pyqtSlot(list)
    def switch_to_main(self,data):
        if(data[0]=='123' and data[1]=='abc'):
            self.widget.addWidget(self.main)
            self.widget.setCurrentWidget(self.main)
            self.screen = QDesktopWidget().screenGeometry()
            self.setGeometry(int((self.screen.width()-1024) / 2),int((self.screen.height() - 600) / 2), 1024, 600)

    @pyqtSlot(list)
    def onSwitched(self,info):
        print(info)
        self.progress = Progress(info[0],info[1],self)
        self.progress.initUi()
        self.main.current_widget.addWidget(self.progress)
        self.main.current_widget.setCurrentWidget(self.progress)
        print("need to remove here  ")
        self.main.lst_url.removeAll()
        self.progress.switch_to_gui.connect(self.onBack)
        self.progress.displayed.connect(self.onDisplay)

    @pyqtSlot(list)
    def onBack(self,items):
        print("--------------")
        print(items)
        self.hLayout = QHBoxLayout()
        self.main.current_widget.setCurrentWidget(self.main.lst_url)
        for item in items:
            for pair in item:
                #check pair
                print("This is url: {0}".format(pair[0]))
                print("This is user: {0}".format(pair[1]))
                self.main.lst_url.addItem(pair[0],pair[1])

        self.main.lst_url.clicked.connect(self.Clicked)


    def Clicked(self):
        item = self.main.lst_url.selectedIndexes()[0]
        print(item)
        self.main.web.load(QUrl(item.data(Qt.DisplayRole)))

        #webbrowser.open_new_tab(item.data(Qt.DisplayRole))

    @pyqtSlot(list)
    def onDisplay(self,pair):
        html = requests.get(pair[0])
        self.keyword = pair[1]
        #print("content")
        #print(html.text)
        #With this solution, poor rendering performance
        self.result_match = re.findall(self.keyword,html.text)
        #print("found")
        #print(self.result_match)
        self.result = re.sub(self.keyword, "<span style='background-color:#FF00FF'>"+ self.keyword+"</span>", html.text,flags=re.IGNORECASE)
        #print("result")
        self.main.web.setHtml(self.result)
        self.keyword = ''
        self.result = ''
        self.result_match = ''
        #self.web.load(QUrl(item))

def main():
    app = QApplication(sys.argv)
    main = main_window()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.FileHandler('test.log')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()