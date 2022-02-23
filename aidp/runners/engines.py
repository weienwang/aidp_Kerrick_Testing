"""This module defines execution engines that will perform work"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from aidp.data.experiments import ClinicalOnlyDataExperiment, ImagingOnlyDataExperiment, \
    FullDataExperiment
import pathlib
import os
import pandas as pd
pd.options.mode.chained_assignment = None  
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import datetime
import numpy as np
import smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv


class Engine(ABC):
    """Abstract Base Class for classes which execute a series of related tasks"""
    _logger = logging.getLogger(__name__)
    experiments = [
            FullDataExperiment(),
            ImagingOnlyDataExperiment(),
            ClinicalOnlyDataExperiment()
        ]

    def __init__(self, model_data):
        self.model_data = model_data
        
    @abstractmethod
    def start(self):
        """Abstract method for executing the engine's tasks"""

class PredictionEngine(Engine):

    """Defines tasks that will be completed as part of the prediction workflow"""

    def start(self, model_key='default'):
        for experiment in self.experiments: # loops through all the experiments
            self._logger.info("Starting prediction experiment: %s", experiment)
            experiment.predict(self.model_data.data, model_key) # this through all the group comparisons
            self._logger.debug("Finished prediction experiment: %s", experiment)

            results = experiment.get_results()
            self.model_data.add_results(results)
            self.model_data.write_output_file()

    def generate_report(self):        
        # get the clinical data and diffusion data
        # need to generate subject-based report
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '/output/'
        subject_ID_list=output_model_data['Subject']
       

        for s in subject_ID_list:
            sub_data=output_model_data.loc[output_model_data['Subject'] == s]
            df1 =sub_data.loc[:,'both_park_v_control (PD/MSA/PSP Probability)':'clinical_psp_v_msa (PSP Probability)']
            df2=df1.transpose()
            df2['Matrics'] = df2.index
            df2.columns = ['Value', 'Matrics']
            df2 = df2.reset_index(drop=True)
            title_name =s+'_Diagnosis_probability'
            df2.plot.bar(x="Matrics", y = "Value",title=s+'_Diagnosis_probability')
            filepath= output_dir + str(title_name) + '.png'
            plt.savefig(filepath , bbox_inches='tight') 
            plt.clf()
            plt.close('all')

    # does not matter what kind of experiments you perform..    
    
    def generate_diagnosis(self):        
        # get the clinical data and diffusion data
        # need to generate subject-based report
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '/output/'
        subject_ID_list=output_model_data['Subject']
        predicted_dignosis = []	
       

        for s in subject_ID_list:

            # for PD
            sub_data=output_model_data.loc[output_model_data['Subject'] == s]

            # # Diagnosis Algorithm Version 1 
            if sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] < 0.5 :
                predicted_dignosis.append('Not Parkinsonism')
            elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] < 0.5 and sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] < 0.5 :
                predicted_dignosis.append('PD')
            elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] < 0.5 :
                predicted_dignosis.append('MSA')
            elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] >= 0.5 :
                predicted_dignosis.append('PSP')
            elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] < 0.5 and sub_data['dmri_psp_v_pd_msa (PSP Probability)'].iloc[0] >= 0.5 or sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] >= 0.5 :
                predicted_dignosis.append('PSP')
            else:
                predicted_dignosis.append('Unknown')

            # Diagnosis Algorithm Version 2
            # if sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] < 0.5 :
            #     predicted_dignosis.append('Not Parkinsonism')
            # elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] < 0.08 and sub_data['dmri_psp_v_pd_msa (PSP Probability)'].iloc[0] < 0.04 and sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] < 0.5 :
            #     predicted_dignosis.append('PD')
            # elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_psp_v_pd_msa (PSP Probability)'].iloc[0] >= 0.3 or sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] >= 0.3 :
            #     predicted_dignosis.append('PSP')
            # elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_psp_v_pd_msa (PSP Probability)'].iloc[0] < 0.5 and sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] < 0.5 and sub_data['dmri_pd_v_msa (PD Probability)'].iloc[0] < 0.5:
            #     predicted_dignosis.append('MSA')
            # elif sub_data['both_park_v_control (PD/MSA/PSP Probability)'].iloc[0] >= 0.5 and sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0] < 0.5 and sub_data['dmri_psp_v_pd_msa (PSP Probability)'].iloc[0] >= 0.5 or sub_data['dmri_psp_v_msa (PSP Probability)'].iloc[0] >= 0.5 :
            #     predicted_dignosis.append('PSP')
            # else:
            #     predicted_dignosis.append('Unknown')


        
        output_model_data['Predicted_diagnosis'] = predicted_dignosis
        filepath=parent_path + '/' + new_filename
        output_model_data.to_excel(filepath)
        
     # create a donut chart
    def donut_chart(self, test_prob, circle_title_1, circle_title_2, switch):       
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '/output/'
        subject_ID_list=output_model_data['Subject']
        

        for s in subject_ID_list:
            sub_data=output_model_data.loc[output_model_data['Subject'] == s]
            if switch == 'Match':
                value = float(sub_data[test_prob])*100

            else:
                value=100-float(sub_data[test_prob])*100
            
            if value >= 50:
                color = [0.9569,0.6941,0.5137]
            else:
                color = [0.8, 0.9, 1]

            first_pie_value = [value, 100 - value]
            
            fig, ax = plt.subplots()  
            
            plt.axis("off")

            # first circle 
            ax = fig.add_subplot(1,2,1)
            x = 0
            y = 0

            my_circle=plt.Circle( (0,0), radius = 0.7, color='white')
            ax.add_patch(my_circle)
            str_1 = str(round(value,1)) + '%'
            label= ax.annotate(str_1, xy=(x,y-0.05), fontsize = 24, ha='center')

            ax.axis('off')
            ax.set_aspect('equal')
            ax.autoscale_view()

            plt.pie(first_pie_value,
                    wedgeprops = { 'linewidth' : 0, 'edgecolor' : 'white' },
                    colors=[color,'#d2d2d2'], startangle = 90, radius=1.2)
            #plt.title("Parkinsonism") 
            #plt.figtext(.3,.8,'PD/MSA/PSP', fontsize=20, ha='center')
            #plt.figtext(.3,.8,'PD', fontsize=20, ha='center')
            plt.figtext(.3,.8,circle_title_1, fontsize=26, ha='center')

            p=plt.gcf()
            p.gca().add_artist(my_circle)

            # second circle 

            second_pro= round(100 - value,1)
            second_pie_value = [100 - value, value] 

            if second_pro >= 50:
                color = [0.9569,0.6941,0.5137]
            else:
                color = [0.8, 0.9, 1]


            ax = fig.add_subplot(1,2,2)
            x = 0
            y = 0

            my_circle=plt.Circle( (0,0), radius = 0.7, color='white')
            ax.add_patch(my_circle)
            str_2 = str(round(second_pro,1)) + '%'
            label= ax.annotate(str_2, xy=(x,y-0.05), fontsize = 24, ha='center')

            ax.axis('off')
            ax.set_aspect('equal')
            ax.autoscale_view()

            plt.pie(second_pie_value,
                    wedgeprops = { 'linewidth' : 0, 'edgecolor' : 'white' },
                    colors=[color,'#d2d2d2'], startangle = 90, radius=1.2)
            #plt.title("Control") 
            #plt.figtext(.72,.8,'Control', fontsize=20, ha='center')
            #plt.figtext(.72,.8,'Atypical', fontsize=20, ha='center')
            plt.figtext(.72,.8,circle_title_2, fontsize=26, ha='center')

            plt.gca().add_artist(my_circle)

            filepath = output_dir + str(s) + '_' +str(circle_title_1) + 'vs' + str(circle_title_2) + '_prob.png'
            plt.savefig(filepath ,orientation='portrait',transparent=True, bbox_inches=None, pad_inches=0,dpi=300)
            plt.clf()
            plt.close('all')

        #plt.savefig('fig2.png',orientation='portrait',transparent=True, bbox_inches=None, pad_inches=0)

    def bar_chart(self):  
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '/output/'
        subject_ID_list=output_model_data['Subject']

        # control data
        control_dir =parent_path + '/control/'
        df= pd.read_excel(control_dir+'1002_Data_Update_Sixflags_Master.xlsx')
        # select control data
        df = df.loc[df.GroupID == 0] 
        df_new =df[["GroupID", "pSN_FW", "Putamen_FW", "Cerebellar_SCP_FW", "Cerebellar_MCP_FW" ]]
        
                # create bar label 
        def add_percent(data):
            if data > 0:
                output = '+'+ str(round(data,1)*100) + '%'
            else:
                output =str(round(data,1)*100) + '%'
            return output
        

        # show label on the bar
        def show_values_on_bars(axs, h_v="v"):
            def _show_on_single_plot(ax):
                if h_v == "v":
                    count = 0
                    for p in ax.patches:
                        _x = p.get_x() + p.get_width() / 2
                        _y = p.get_y() + p.get_height() +0.04
                        value = label[count]
                        count+=1
                        ax.text(_x, _y, value, ha="center", size = 12) 

            if isinstance(axs, np.ndarray):
                for idx, ax in np.ndenumerate(axs):
                    _show_on_single_plot(ax)
            else:
                _show_on_single_plot(axs)


        for s in subject_ID_list:
        
            true_sub_data=output_model_data.loc[output_model_data['Subject'] == s]
                       
            # concat control and subject data 
            sub_data=true_sub_data.copy()
            sub_data['GroupID'].iloc[0] = '1'
            sub_data =sub_data[['GroupID', "pSN_FW", "Putamen_FW", "Cerebellar_SCP_FW", "Cerebellar_MCP_FW" ]]
            combined=pd.concat([df_new, sub_data], axis=0, ignore_index=True)

            #wide to long             
            combined.set_index('GroupID')
            combined = combined.reset_index()
            long_df=pd.melt(combined, id_vars='GroupID', value_vars=[ "pSN_FW", "Putamen_FW", "Cerebellar_SCP_FW", "Cerebellar_MCP_FW" ])
            stats=long_df.groupby(['GroupID', 'variable']).mean()
        
          
            # set the matlab figure
            plt.figure(figsize=(7,3))
            #sns.set(rc={'figure.figsize':(7,3)})
            #sns.set_style("whitegrid")
            sns.set_style("dark")
            sns.set_context("talk")
            colors = ['#4c72b0', '#55a868'] # Set your custom color palette
            sns.set_palette(sns.color_palette(colors))

            # make a bar plot
            g= sns.barplot(x="variable",y="value", hue = "GroupID", data=long_df, capsize=.1 )
            plt.legend([],[], frameon=False)

            g.set_xticklabels(["pSN", "Putamen", "SCP" , "MCP"])
            g.set(xlabel='ROIs', ylabel='Free water')
            plt.gca().set_prop_cycle(None)

            #print(stats.loc[('1', 'Cerebellar_MCP_FW')].value)
            #print(stats.loc[(0, 'Cerebellar_MCP_FW')].value)
            # this is so interesting!!

            Cerebellar_MCP_FW_dif=add_percent((stats.loc[('1', 'Cerebellar_MCP_FW')].value-stats.loc[(0, 'Cerebellar_MCP_FW')].value)/stats.loc[(0, 'Cerebellar_MCP_FW')].value)
            Cerebellar_SCP_FW_dif=add_percent((stats.loc[('1', 'Cerebellar_SCP_FW')].value-stats.loc[(0, 'Cerebellar_SCP_FW')].value)/stats.loc[(0, 'Cerebellar_SCP_FW')].value)
            Putamen_FW_dif=add_percent((stats.loc[('1', 'Putamen_FW')].value-stats.loc[(0, 'Putamen_FW')].value)/stats.loc[(0, 'Putamen_FW')].value)
            pSN_FW_dif=add_percent((stats.loc[('1', 'pSN_FW')].value-stats.loc[(0, 'pSN_FW')].value)/stats.loc[(0, 'pSN_FW')].value)
            label= ["", "", "", "", pSN_FW_dif, Putamen_FW_dif, Cerebellar_SCP_FW_dif,Cerebellar_MCP_FW_dif ]
          
    
            show_values_on_bars(g, "v")


            filepath = output_dir + str(s) + '_FW_barplot.png'
            plt.savefig(filepath ,orientation='landscape',transparent=True, bbox_inches='tight', pad_inches=0, dpi=300)
            #plt.show()
            plt.clf()
            plt.close('all')
    

    def pdf_report(self):  
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '/output/'
        subject_ID_list=output_model_data['Subject']
        
        for s in subject_ID_list:
            sub_data=output_model_data[output_model_data["Subject"] == s]
            
            ID=sub_data['Subject'].iloc[0]
            print(ID)
            Age=sub_data['Age'].iloc[0]
            Sex=sub_data['Sex'].iloc[0]

            Sex=sub_data['Sex'].iloc[0]
            predicted_diagnosis=sub_data['Predicted_diagnosis'].iloc[0]
            MSA_PSP_Pro=sub_data['dmri_msa_psp_v_pd (MSA/PSP Probability)'].iloc[0]

            if Sex == 0:
                Sex_interp = 'Male'
            else:
                Sex_interp = 'Female'            

            UPDRS=sub_data['UPDRS'].iloc[0]   

            pdf = FPDF('P', 'mm', 'Letter')
            pdf.add_page()
            pdf.set_font('Arial', '', 16)
            parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
            output_dir=parent_path + '/output/'
            template_dir=parent_path + '/resources/'

            #output_dir="c:\\users\\weienwang\\onedrive\\documents\\github\\aidp_BETA\\output\\"
            #template_dir="c:\\users\\weienwang\\onedrive\\documents\\github\\aidp_BETA\\resources\\"
            # select differnet report layout for different diagnosis


            if MSA_PSP_Pro >= 0.5 and (predicted_diagnosis == 'PSP' or predicted_diagnosis == 'MSA'):
                
                #pdf.image(template_dir+"template_v2-600.png",x = 0, y = 0, w = 215.9, h = 279.4)
                pdf.image(template_dir+"template-150_v3.png",x = 0, y = 0, w = 215.9, h = 279.4)


                pdf.set_xy(82, 30)
                pdf.cell(25, 30, ID)

                pdf.set_xy(82, 43)
                date_output=datetime.datetime.now().strftime("%m-%d-%Y")
                pdf.cell(25, 30, date_output)


                clinical='Age: '+str(Age) + '   Sex: '+ str(Sex_interp) + '   UPDRS: ' + str(UPDRS)
                pdf.set_xy(82, 56)
                pdf.cell(25, 30, clinical)

                filepath = output_dir + str(ID) + str('_PD · MSA · PSPvsControl_prob.png')
                pdf.image(filepath,x = 145, y = 80.71, w =68.069, h = 51.052)

                filepath = output_dir + str(ID) +  str('_PDvsMSA · PSP_prob.png')
                pdf.image(filepath,x = 145, y = 112.71, w = 68.069, h =51.052)

                filepath = output_dir + str(ID) + str('_MSAvsPSP_prob.png')
                pdf.image(filepath,x = 145, y = 144.71 , w = 68.069, h =51.052)


                filepath = output_dir + str(ID) + str('_FW_barplot.png')
                pdf.image(filepath,x = 15.25, y = 215.4 , w = 111.040, h = 55.728)

                pdf.set_xy(88, 172)
                pdf.cell(25, 30, predicted_diagnosis)

                file_name=output_dir + str(ID) + '_Imaging_Report.pdf'
                pdf.output(file_name, 'F')
            
            elif predicted_diagnosis == 'PSP' and MSA_PSP_Pro < 0.5 :
                
                #pdf.image(template_dir+"template_v2-600.png",x = 0, y = 0, w = 215.9, h = 279.4)
                pdf.image(template_dir+"template-150_v3_PSP.png",x = 0, y = 0, w = 215.9, h = 279.4)


                pdf.set_xy(82, 30)
                pdf.cell(25, 30, ID)

                pdf.set_xy(82, 43)
                date_output=datetime.datetime.now().strftime("%m-%d-%Y")
                pdf.cell(25, 30, date_output)


                clinical='Age: '+str(Age) + '   Sex: '+ str(Sex_interp) + '   UPDRS: ' + str(UPDRS)
                pdf.set_xy(82, 56)
                pdf.cell(25, 30, clinical)

                filepath = output_dir + str(ID) + str('_PD · MSA · PSPvsControl_prob.png')
                pdf.image(filepath,x = 145, y = 80.71, w =68.069, h = 51.052)

                filepath = output_dir + str(ID) +  str('_PSPvsPD · MSA_prob.png')
                pdf.image(filepath,x = 145, y = 112.71, w = 68.069, h =51.052)        

                filepath = output_dir + str(ID) + str('_MSAvsPSP_prob.png')
                pdf.image(filepath,x = 145, y = 144.71 , w = 68.069, h =51.052)


                filepath = output_dir + str(ID) + str('_FW_barplot.png')
                pdf.image(filepath,x = 15.25, y = 215.4 , w = 111.040, h = 55.728)

                pdf.set_xy(88, 172)
                pdf.cell(25, 30, predicted_diagnosis)

                file_name=output_dir + str(ID) + '_Imaging_Report.pdf'
                pdf.output(file_name, 'F')


            elif predicted_diagnosis == 'PD':

                pdf.image(template_dir+"template-150_v3_PD.png",x = 0, y = 0, w = 215.9, h = 279.4)
                pdf.set_xy(82, 30)
                pdf.cell(25, 30, ID)

                pdf.set_xy(82, 43)
                date_output=datetime.datetime.now().strftime("%m-%d-%Y")
                pdf.cell(25, 30, date_output)

                clinical='Age: '+str(Age) + '   Sex: '+ str(Sex_interp) + '   UPDRS: ' + str(UPDRS)
                pdf.set_xy(82, 56)
                pdf.cell(25, 30, clinical)

                filepath = output_dir + str(ID) + str('_PD · MSA · PSPvsControl_prob.png')
                pdf.image(filepath,x = 145, y = 80.71, w =68.069, h = 51.052)

                filepath = output_dir + str(ID) +  str('_PDvsMSA · PSP_prob.png')
                pdf.image(filepath,x = 145, y = 112.71, w = 68.069, h =51.052)

                filepath = output_dir + str(ID) + str('_FW_barplot.png')
                pdf.image(filepath,x = 15.25, y = 215.4 , w = 111.040, h = 55.728)

                pdf.set_xy(88, 172)
                pdf.cell(25, 30, predicted_diagnosis)

                file_name=output_dir + str(ID) + '_Imaging_Report.pdf'
                pdf.output(file_name, 'F')
            else:

                pdf.image(template_dir+"template-150_v3_Control.png",x = 0, y = 0, w = 215.9, h = 279.4)
                pdf.set_xy(82, 30)
                pdf.cell(25, 30, ID)

                pdf.set_xy(82, 43)
                date_output=datetime.datetime.now().strftime("%m-%d-%Y")
                pdf.cell(25, 30, date_output)

                clinical='Age: '+str(Age) + '   Sex: '+ str(Sex_interp) + '   UPDRS: ' + str(UPDRS)
                pdf.set_xy(82, 56)
                pdf.cell(25, 30, clinical)

                filepath = output_dir + str(ID) + str('_PD · MSA · PSPvsControl_prob.png')
                pdf.image(filepath,x = 145, y = 80.71, w =68.069, h = 51.052)

                filepath = output_dir + str(ID) + str('_FW_barplot.png')
                pdf.image(filepath,x = 15.25, y = 215.4 , w = 111.040, h = 55.728)
                
                pdf.set_xy(88, 172)
                pdf.cell(25, 30, predicted_diagnosis)

                file_name=output_dir + str(ID) + '_Imaging_Report.pdf'
                pdf.output(file_name, 'F')

    def send_report(self, switch): 
        
        parent_path=str(pathlib.Path(__file__).parent.parent.parent) 
        new_filename = '%s_out.xlsx' %os.path.splitext(os.path.basename(self.model_data.filename))[-2]
        output_model_data = pd.read_excel(parent_path + '/' + new_filename).drop('Unnamed: 0',axis=1)
        output_dir=parent_path + '\\output\\'
        subject_ID_list=output_model_data['Subject']
        if switch == '1':
            print("sending")
            for ID in subject_ID_list:

                file_name=output_dir + str(ID) + '_Imaging_Report.pdf'
                pdf_file_name = str(ID) + '_Imaging_Report.pdf'
                # set up file and working directory
                port = 465  # For SSL
                #password = input("Type your password and press enter: ")
                password='image502L1'
                # read contacts 

                with open("c:\\users\\weienwang\\onedrive\\documents\\github\\aidp_BETA\\sendemail\\"+"email_contacts.csv") as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header row
                    for name, email in reader:
                        print(f"Sending email to {name}")

                        # Create a secure SSL context
                        context = ssl.create_default_context()
                        sender_email = "aidp.imaging@gmail.com"

                        date_output=datetime.datetime.now().strftime("%m-%d-%Y")
                        message = MIMEMultipart("alternative")
                        message["Subject"] = 'AIDP Report-' + ID + '-'+ date_output
                        message["From"] = "aidp.imaging@gmail.com"
                        message["To"] = "weienwang@ufl.edu"

                        # add attachement to the email
                        # Open PDF file in binary mode
                        with open(file_name, "rb") as attachment:
                            # Add file as application/octet-stream
                            # Email client can usually download this automatically as attachment
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())

                        # Encode file in ASCII characters to send by email    
                        encoders.encode_base64(part)

                        # Add header as key/value pair to attachment part
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {pdf_file_name}",
                        )

                        # Add attachment to message and convert message to string
                        message.attach(part)

                        # Create the plain-text and HTML version of your message
                        text = """\

                        Hi User, 

                        New dMRI images have been uploaded!

                        Please see the imaging biomarker report in the attached PDF.

                        For more details, please visit our webiste: https://medx.digitalworlds.ufl.edu/AIDP/

                        """
                        html = """\
                        <html>
                        <body>
                            <p style="font-family:Verdana;background-color:rgb(255, 255, 237);font-size:100%;">Hi {name},
                                <br>
                                <br>New dMRI images have been uploaded!
                                <br>
                                <br>Please see the biomarker report for patient ID {ID} as attached.<br>
                                <br>
                                For more information, please visit the website: 
                                <a href="https://medx.digitalworlds.ufl.edu/AIDP/"> AIDP Portal </a> 
                                <br>
                                <br>
                                <br>Thank you,
                                <br> 
                                <br>Automated Imaging Differentiation of Parkinsonism (AIDP) Team
                                <br>
                                <br>-------
                                <br>Questions?
                                <br>Contact- Wei-en Wang, weienwang@ufl.edu 


                            </p>
                        </body>
                        </html>
                        """
                        html=html.format(name=name, ID=ID)

                        # Turn these into plain/html MIMEText objects
                        part1 = MIMEText(text, "plain")
                        part2 = MIMEText(html, "html")

                        # Add HTML/plain-text parts to MIMEMultipart message
                        # The email client will try to render the last part first
                        message.attach(part1)
                        message.attach(part2)

                        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                            server.login(sender_email, password)
                            server.sendmail(
                                sender_email, email, message.as_string()
                            )
        
                            server.quit()
        else:
            print('Did not send report emails')


class TrainingEngine(Engine):
    """Defines tasks that will be completed as part of the training workflow"""
    def start(self, model_key = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S%f")):
        for experiment in self.experiments:
            self._logger.info("Starting training experiment: %s", experiment)
            experiment.train(self.model_data.data, model_key)
            self._logger.debug("Finished training experiment: %s", experiment)
    def generate_report(self):
        pass
    def donut_chart(self, test_prob, circle_title_1, circle_title_2, switch):
        pass
    def bar_chart(self):
        pass
    def pdf_report(self):
        pass
    def generate_diagnosis(self):
        pass 
    def send_report(self, switch): 
        pass



def getEngine(key, model_data):
    logger = logging.getLogger(__name__)

    if key == 'predict':
        return PredictionEngine(model_data)
    if key == 'train':
        return TrainingEngine(model_data)
    else:
        logger.error("Use of unsupported Engine key: %s", key)
        raise NotImplementedError
        

   