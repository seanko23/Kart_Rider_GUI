import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import pandas as pd
import numpy as np
from sklearn import preprocessing
from scipy.stats import norm
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk) 
import os





df = pd.read_csv("kartriderdataset.csv",sep=",")

sorter = len(df.iloc[:,1:].columns)+2

#Below lines convert m:s:ms format to float

column_names = list(df.columns)[1:]

for i in column_names:
    measured_times = []
    for j in df[i]:     
        j = [int(z) for z in j.split(":")]
        updated_time = float(str(j[0]*60+j[1])+"."+str(j[2]))
        measured_times.append(updated_time)
    df[i] = measured_times


for i in df.iloc[:,1:]:
    scaled_values = (-(df[i] - df[i].max())/(df[i].max() - df[i].min()))
    new_column_name = 'scaled_' + i
    df[new_column_name] = scaled_values


sum_of_records_list = []
for i in df.iterrows():
    sum_of_records = 0
    for j in i[1][1:sorter]:
        sum_of_records+=j
    sum_of_records_list.append(sum_of_records)

mean_value = np.mean(sum_of_records_list)

for i in range(len(sum_of_records_list)):
    sum_of_records_list[i] = mean_value - sum_of_records_list[i]
    
df['Record_Sum'] = sum_of_records_list

normalized_values = preprocessing.scale(df['Record_Sum'])
df['ELO'] = normalized_values*100 + 4000
df['scaled_average'] = np.nan

# Parameters for the data
mu, std = norm.fit(df['ELO'])

# Show the user the percentile that he or she is in

new_df = df.sort_values(by=['ELO']).reset_index(drop=True)

ranking_df = new_df[['IGN','ELO']].iloc[::-1].reset_index(drop=True)


# This is the start of GUI

class KrEloApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("640x500+300+200")
        self._frame = None
        self.switch_frame(StartPage)
        self.title("Kart Rider Rush Plus ELO Viewer")
    
    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack()
        
    
class StartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.entry_var=""
        tk.Label(self, text = "What is the IGN: ").pack(fill="x", pady=10)
        self.ignEntry = tk.Entry(self)
        self.ignEntry.pack()
        self.ignEntry.focus_set()
        tk.Button(self, text = "Search", command=lambda: self.save_and_switch_frame(master,EloPage)).pack(side="bottom",expand=True)


    def save_and_switch_frame(self,master, frame_class):
        global ign
        ign = self.ignEntry.get()
        counter = 0
        #Checks if the dataframe contains the IGN that I am looking for
        for i in df['IGN']:
            counter+=1
            if i == ign:
                master.switch_frame(frame_class)
                break
            elif counter == len(df['IGN']):
                msgbox.showerror("Error","Entered IGN does not exist!")
                break



class EloPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text = "Your ELO is: "+self.display_elo() + " top " + self.percentile_and_rank()).pack(fill="x",pady=10)
        tk.Button(self, text = "Would you like to view your standing in chart?", command = lambda: master.switch_frame(ChartPage)).pack(expand= True)
        tk.Button(self, text = "Would you like to view your standing in graph?", command=lambda: self.show_graph()).pack(expand=True)
        tk.Button(self, text = "Areas you can improve on", command = lambda: master.switch_frame(AdvicePage)).pack(expand= True)
        tk.Button(self,text="Try different IGN", command=lambda: master.switch_frame(StartPage)).pack(expand=True)

    def display_elo(self):
        # Output the ELO
        global my_ELO
        for i in df['IGN']:
            if i == ign:
                my_ELO = float((df[df['IGN'] == i]['ELO']).values)
        self.my_ELO_for_display = str(int(round(my_ELO,0)))
        return self.my_ELO_for_display

    def percentile_and_rank(self):
        self.my_ranking = new_df.loc[new_df['IGN']==ign].index.values[0]+1
        self.my_percentile = str(round(((self.my_ranking)/len(new_df.index))*100,1))
        self.my_actual_ranking = str(len(new_df.index) - self.my_ranking + 1)
        return self.my_percentile +" percentile and ranked "+self.my_actual_ranking +"!"

    def show_graph(self):
        bins_size = int(np.ceil(np.sqrt(len(df['IGN']))))
        df.ELO.plot.kde()
        n, bins, patches = plt.hist(df['ELO'],bins=bins_size,density=True,alpha=0.7,color='g',edgecolor='black', linewidth=1.2)
        for i in range(len(patches))[::-1]:
            if round(patches[i].get_x(),2) <= round(my_ELO,2):
                patches[i].set_color('b')
                break
            else:
                pass
        plt.title("Kart Rider Rush Plus ELO for given sample (average ELO is "+ str(np.ceil(mu)) +")\n(The blue colored bin is where " + ign + " is relatively ranked at)")
        plt.xlabel("ELO")
        plt.ylabel("Density")

        return plt.show()
        

    
        

class ChartPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        tk.Label(self, text="Ranking Chart").pack(fill = "x", pady=10)
        tk.Button(self,text="Go back to the previous page", command=lambda: master.switch_frame(EloPage)).pack(expand=True)
        tk.Button(self,text="Show my underperformed tracks", command=lambda: master.switch_frame(AdvicePage)).pack(expand=True)

        #Inputting chart that displays ranks
        frame = tk.Frame(self)
        frame.pack()

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right",fill="y")

        rank_chart = tk.Text(frame,height=25, yscrollcommand = scrollbar.set)
        rank_chart.insert(tk.END, self.show_chart())
        rank_chart.tag_configure("center", justify='center')
        rank_chart.tag_add("center", "1.0", "end")
        rank_chart.pack(fill="both",expand=True)

        scrollbar.config(command=rank_chart.yview)
        tk.Button(self, text="Download the chart as Excel file", command = lambda: self.download_chart()).pack(expand=True)




    def show_chart(self):
        global final_ranking_df
        ranking_df['ELO'] = round(ranking_df['ELO'],0).astype(int)
        self.ranking_list = [i+1 for i in range(len(ranking_df))]
        ranking_df['Rank'] = self.ranking_list
        self.cols = ranking_df.columns.tolist()
        self.cols = self.cols[-1:] + self.cols[:-1]
        final_ranking_df=ranking_df[self.cols]
        return final_ranking_df.to_string(index=False)

    def download_chart(self):
        return final_ranking_df.to_excel('ranking_chart.xlsx', index=False)
        
        


class AdvicePage(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        frame = tk.Frame(self)
        frame.pack()
        #tk.Label(frame, text=self.get_advice()).pack(fill="x", pady=10)
        advice = tk.Text(frame, height = 25)
        advice.insert(tk.END, self.get_advice())
        advice.tag_configure("center", justify='center')
        advice.tag_add("center", "1.0", "end")
        advice.pack(fill="both",expand=True)

        tk.Button(self,text="Go back to the previous page", command=lambda: master.switch_frame(EloPage)).pack(expand=True)

# Returns the string of maps the user is underperforming compared to the personal records of other maps

    def get_advice(self):
        average_list = []

        for i in df.iterrows():
            average_list.append(i[1][sorter-1:sorter*2-3].mean()) # The numbers 8:14 represents scaled_something columns

        df['scaled_average'] = average_list

        user_data_row = df.loc[df['IGN']==ign]

        scaled_column_list = []
        for i in df.columns:
            if "scaled" in i:
                scaled_column_list.append(i)

        user_average = user_data_row[scaled_column_list[-1]]

        maps_to_improve=[]
        comparative_records = []

        for i in scaled_column_list[0:-1]:
            if (float(user_data_row[i]) - float(user_average)) < 0:
                maps_to_improve.append(i)
                comparative_records.append(float(user_data_row[i]))
            else:
                pass

        user_records_dict = dict(zip(maps_to_improve,comparative_records))

        user_records_dict = {k: v for k, v in sorted(user_records_dict.items(), key=lambda item: item[1])}

        maps_to_improve_ordered = list(user_records_dict.keys())

        final_maps_to_improve = []

        for i in maps_to_improve_ordered:
            final_maps_to_improve.append(i.replace('scaled_',''))

        #Ordered from the worst underperformed map to best underperformed map
        #print(final_maps_to_improve)

        final_string = 'Your underperformed tracks: '

        for i in final_maps_to_improve:
            if i != final_maps_to_improve[-1]:
                final_string = final_string + i + ', '
            else:
                final_string = final_string[:-2] + ' and ' + i + '\n\n\n\nNote:\nMaps are listed from comparatively worst performing to decent performing tracks'

        return final_string
    
    
        
        
#if __name__ == "__main__":

app = KrEloApp()
app.mainloop()
    
    