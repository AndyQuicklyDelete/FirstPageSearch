
from kivy.config import Config
Config.set('graphics', 'verify_gl_main_thread', 0)
Config.set('input', 'mouse', 'mouse,disable_multitouch')
#Config.set('graphics', 'resizable', False)

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.uix.image import Image
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList
from kivymd.uix.list import OneLineListItem
from kivy.core.window import Window
import kivymd.icon_definitions

from pydal import DAL
import os, webbrowser, time
import threading
import platform

if platform.system() == "Darwin":
    os.chdir(sys._MEIPASS)



db = DAL('sqlite://internetdb.db', auto_import=True)

Window.size = (720, 760)
# Window.minimum_width = 520
# Window.minimum_height = 410


import configparser
Configy = configparser.ConfigParser()
    
if not os.path.exists('settings.ini'):
    Configy.set('DEFAULT', 'mode', 'Light')
    Configy.write(open('settings.ini', 'w'))
    Configy.read("settings.ini")
else:
    Configy.read("settings.ini")

results_limit = None

class MainInterface(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(self.build()) 


    def build(self):
        screen = MDScreen()
        self.default_mode = str(Configy.get('DEFAULT', 'mode'))

        self.theme_cls.theme_style = self.default_mode
        self.theme_cls.primary_palette = "Blue"

        layout = MDRelativeLayout()

        self.img = Image(source="branding.png", size_hint=(.20, .20), pos_hint = {'center_x': 0.5, 'center_y': 0.92})
        
        self.limitLabel = MDLabel(text="Check to limit the search results to 10",
                                pos_hint = {'center_y': 0.81},
                                halign="center", 
                                font_style = "H6")
        
        self.checkLimit = MDCheckbox(size_hint = (None, None), pos_hint = {'center_x': .5, 'center_y': 0.78}) 

        self.checkLimit.bind(on_release = lambda x: self.on_checkbox_active(x, x.active, "100LIMIT"))

        # self.exactLabel = MDLabel(text="Check to use whole phrase in search",
        #                         pos_hint = {'center_y': 0.75},
        #                         halign="center", 
        #                         font_style = "H6")
        
        # self.checkExact = MDCheckbox(size_hint = (None, None), pos_hint = {'center_x': .5, 'center_y': 0.71}) 

        # self.checkExact.bind(on_release = lambda x: self.on_checkbox_exact(x, x.active, "EXACTLIMIT"))

        self.linkInput = MDTextField(text='', mode="round", pos_hint = {'center_x': 0.5, 'center_y': 0.72}, 
                                     size_hint_x = 0.93, font_size = "24sp", write_tab = False, multiline=False, 
                                     on_text_validate = self.getSearchInfo, font_name="DroidSansFallback.ttf") #  lambda instance: self.searchInfoThread(instance) 

        self.linkButton = MDRaisedButton(text='Search the Web', pos_hint = {'center_x': 0.35, 'center_y': 0.64}, font_size = "24sp", font_name="DroidSansFallback.ttf")
        self.linkButton.bind(on_release = self.getSearchInfo)

        self.themeButton = MDRaisedButton(text='Light/Dark Mode', pos_hint = {'center_x': 0.65, 'center_y': 0.64}, font_size = "24sp", font_name="DroidSansFallback.ttf")
        self.themeButton.bind(on_release = self.getThemeInfo)

        # self.modeInformationLabel = MDLabel(text="", pos_hint = {'center_x': 0.5, 'center_y': 0.50}, halign = "center", font_style = "H6")
        self.resultsCountLabel = MDLabel(text="", pos_hint = {'center_x': 0.5, 'center_y': 0.54}, halign = "center", font_style = "H6")
        
        self.totalCount = db(db.domains.id > 0).count()
        self.totalCount = "{:0,}".format(self.totalCount)
        db.commit()

        self.sitesCountLabel = MDLabel(text="We have currently indexed {0} websites".format(self.totalCount), 
                                       pos_hint = {'center_x': 0.5, 'center_y': 0.58}, halign = "center")

        self.dataTables = MDScrollView(
            MDList(id="container"),
            size_hint=(.90, .54),
            pos_hint = {'center_x': 0.5, 'center_y': 0.25}
        )


        layout.add_widget(self.img)
        layout.add_widget(self.limitLabel)
        layout.add_widget(self.checkLimit)
        # layout.add_widget(self.exactLabel)
        # layout.add_widget(self.checkExact)
        layout.add_widget(self.linkInput)
        layout.add_widget(self.linkButton)
        layout.add_widget(self.themeButton)
        layout.add_widget(self.resultsCountLabel)
        # layout.add_widget(self.modeInformationLabel)
        layout.add_widget(self.sitesCountLabel)
        layout.add_widget(self.dataTables)
        screen.add_widget(layout)
        return screen


    def on_checkbox_active(self, checkbox, active, value):
        global results_limit

        if checkbox.state == "down":
            results_limit = "100LIMIT"
        elif checkbox.state == "normal":
            results_limit = "NOLIMIT"
        else:
            results_limit = "NOLIMIT"

    # def on_checkbox_exact(self, checkbox, active, value):
    #     global results_exact

    #     if checkbox.state == "down":
    #         results_exact = "EXACTLIMIT"
    #     elif checkbox.state == "normal":
    #         results_exact = "NOEXACT"
    #     else:
    #         results_exact = "NOEXACT"

    def update_ui(self, link_code):
        
        self.dataTables.ids.container.clear_widgets()

        countOfWords = len(link_code.split())

        # 

        if results_limit != None and results_limit != "NOLIMIT": 
            if results_limit == "100LIMIT":
                if countOfWords == 1:
                    query_code = "(db.domains.title.like('%'+str(link_code)+'%'))"
                    self.query = db(eval(query_code)).select(db.domains.ALL, limitby=(0, 10))

                if countOfWords > 1:
                    link_code = link_code.split()
                    query_code = "(db.domains.title.like('%'+str(link_code[0])+'%')) & "

                    for i in range(countOfWords):
                        query_code += "(db.domains.title.like('%'+str(link_code[i])+'%')) & "

                    query_code = query_code[:-3]
                    self.query = db(eval(query_code)).select(db.domains.ALL, limitby=(0, 10))
        else:
            if countOfWords == 1:
                query_code = "(db.domains.title.like('%'+str(link_code)+'%'))"
                self.query = db(eval(query_code)).select(db.domains.ALL, limitby=(0, 200))

            if countOfWords > 1:
                link_code = link_code.split()
                query_code = "(db.domains.title.like('%'+str(link_code[0])+'%')) & "

                for i in range(countOfWords):
                    query_code += "(db.domains.title.like('%'+str(link_code[i])+'%')) & "

                query_code = query_code[:-3]
                self.query = db(eval(query_code)).select(db.domains.ALL, limitby=(0, 200))

        for row in self.query:

            # if link_code in row.title[0:60]:
            #     highlight_text = (127/255, 17/255, 224/255, 1)
            # else:
            #     highlight_text = None

            # enc_str = str(row.title).encode(encoding = 'UTF-8', errors = 'ignore')
            # dec_string = enc_str.decode("utf-8")

            self.dataTables.ids.container.add_widget(OneLineListItem(
                text="[font=DroidSansFallback.ttf]" + str(row.title).strip() + "[/font]",
                # theme_text_color="Custom",
                # text_color = highlight_text,
                secondary_text=str(row.path).strip(),
                on_release=self.on_row_press))
            time.sleep(0.08)

        db.commit()
        
        self.dataTables.ids.container.add_widget(OneLineListItem(text="\n\n"))        
        

    def getSearchInfo(self, instance):
        
        # self.modeInformationLabel.text = ""
        self.resultsCountLabel.text = ""
        self.link = str(self.linkInput.text.strip())

        if self.link == None or self.link == "":
            pass
        elif self.link != "" or self.link != None:
            countOfWords = len(self.link.split())
        
            if countOfWords == 1:
                query_code = "(db.domains.title.like('%'+str(self.link)+'%'))"
                self.count = db(eval(query_code)).count()
                db.commit()

            if countOfWords > 1:
                link_code = self.link.split()
                query_code = "(db.domains.title.like('%'+str(link_code[0])+'%')) & "

                for i in range(countOfWords):
                    query_code += "(db.domains.title.like('%'+str(link_code[i])+'%')) & "

                query_code = query_code[:-3]
                self.count = db(eval(query_code)).count()

                db.commit()

            self.resultsCountLabel.font_name = "DroidSansFallback.ttf"
                           

            # if results_limit != None and results_limit != "NOLIMIT": 
            #     if results_limit == "100LIMIT":
            #         self.resultsCountLabel.text = "Number of results: " + str(self.count) + " for search query: " + self.link + " and returned 10"
            # else:
            self.resultsCountLabel.text = "Number of results: " + str(self.count) + " for search query: " + self.link

            self.resultsCountLabel.halign = 'center'
            self.resultsCountLabel.pos_hint = {'center_x': 0.5, 'center_y': 0.54}

            threading.Thread(target=self.update_ui, args=(self.link, ), daemon=True).start()       

            self.linkInput.text = ""

        else:
            pass

    
    def getThemeInfo(self, instance):
        # self.resultsCountLabel.text = ""
        # self.modeInformationLabel.text = ""

        self.mode = Configy.get('DEFAULT', 'mode')
        self.mode = str(self.mode)

        if self.mode == "Light":
            Configy.set('DEFAULT', 'mode', 'Dark')
            self.theme_cls.theme_style = 'Dark'
        if self.mode == "Dark":
            Configy.set('DEFAULT', 'mode', 'Light')
            self.theme_cls.theme_style = 'Light'
        if self.mode == "" or self.mode == None:
            Configy.set('DEFAULT', 'mode', 'Light')
            self.theme_cls.theme_style = 'Light'
        
        with open('settings.ini', 'w') as configfile:
            Configy.write(configfile)

        # self.modeInformationLabel.text = "Requires App Restart"
        # self.modeInformationLabel.halign = 'center'
        # self.modeInformationLabel.pos_hint = {'center_x': 0.5, 'center_y': 0.50}

    
    def on_row_press(self, path):
        path = path.secondary_text
        webbrowser.open(path, new=2, autoraise=True)


class MainApp(MDApp):
    def build(self):
        self.title = "FirstPageSearch - 1.0"
        self.icon = 'branding.png'
        self.focus = True
        return MainInterface()    


if __name__ == '__main__':
    MainApp().run()    

