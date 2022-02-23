"""This module defines the different data experiments.

    Experiments are defined by what data is used when creating models.
    Some subset of the input data is used for each experiment.
 """
import logging
import pathlib
from abc import ABC, abstractmethod
import pandas as pd
from aidp.data.groupings import ParkinsonsVsControlGrouping, MsaPspVsPdGrouping, MsaVsPdPspGrouping, PspVsPdMsaGrouping, PspVsMsaGrouping, PdVsMsaGrouping
from aidp.ml.predictors import Predictor, LinearSvcPredictor
from aidp.report.writers import LogReportWriter
import itertools

class DataExperiment(ABC):
    key = None
    groupings = [
        ParkinsonsVsControlGrouping(),
        MsaPspVsPdGrouping(),
        MsaVsPdPspGrouping(),
        PspVsPdMsaGrouping(),
        PspVsMsaGrouping(),
        PdVsMsaGrouping()
   
    ]
   
    report_writer = LogReportWriter()

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def filter_data(self, data):
        pass #pragma: no cover

    def predict(self, data, model_key):
        self._logger.info("Starting model prediction")
        filtered_data = self.filter_data(data)
        for grouping in self.groupings:
            predictor = Predictor()
            predictor.load_model_from_file(self.key, grouping.key, model_key)
            grouping.predictions = predictor.make_predictions(filtered_data)
        self._logger.info("Starting model prediction")


    def train(self, data, model_key, save_models=True):
        self._logger.info("Starting model training")
        #TODO: Implement Training mechanism
        filtered_data = self.filter_data(data)

        master_outcome_num = []	
        master_outcome_grp = []	

        for grouping in self.groupings:
            grouping.group_data(filtered_data).grouped_data
            self._logger.debug("Training model for grouping: %s", grouping.key)
            trainer = LinearSvcPredictor()
            trainer.train_model(grouping.grouped_data) 
            # Write report of the results
            training_output, validation_output = self.report_writer.write_report(trainer.classifier.best_estimator_, trainer.X_train, trainer.Y_train, trainer.X_test, trainer.Y_test)
            
            # make a group list
            master_outcome_grp.append(grouping.key)

            # make a data list
            combined_data = list(itertools.chain.from_iterable([training_output, validation_output]))           
           
            # make it to small datafram and transpose
            smalldataframe = pd.DataFrame(combined_data)

            # append small dataframs
            master_outcome_num.append(smalldataframe.transpose())
            # Write model to pickle file
            if save_models:
                trainer.save_model_to_file(self.key, grouping.key, model_key)
        # save the master outcome
        Group_df = pd.DataFrame({'Group':master_outcome_grp})
        master_outcome_num_df = pd.concat(master_outcome_num, ignore_index=True)
   
        # column bind x            
        master_outcome_num_bigdataframe = pd.concat([Group_df, master_outcome_num_df], axis=1, ignore_index=True)
        parent_path=str(pathlib.Path(__file__).parent.parent.parent)
        filepath = parent_path + "/" + str(model_key) + '_' + str(self.key) + '_Training_Performance.csv'
        master_outcome_num_bigdataframe.to_csv(filepath, header= ['Group', 'recall_t', 'precision_t', 'auc_t', 'specificity_t', 
            'npv_t', 'accuracy_t', 'weighted_sensitivity_t', 'weighted_ppv_t', 'weighted_specificity_t' ,
            'weighted_npv_t', 'weighted_accuracy_t', 'recall_v', 'precision_v', 'auc_v', 'specificity_v', 
            'npv_v', 'accuracy_v', 'weighted_sensitivity_v', 'weighted_ppv_v', 'weighted_specificity_v' ,
            'weighted_npv_v', 'weighted_accuracy_v'])
  
        self._logger.debug("Finished model training")       

    def get_results(self):
        # TODO: Add tests
        results = pd.DataFrame()
        for grouping in self.groupings:
            column = '%s_%s (%s Probability)' %(self.key, grouping.key, grouping.positive_label)
            results[column] = grouping.predictions

        return results

    def __str__(self):
        return type(self).__name__

class ClinicalOnlyDataExperiment(DataExperiment):
    key = "clinical"

    def filter_data(self, data):
        standard_data = get_standardized_data(data)
        return standard_data[['GroupID', 'Age', 'Sex', 'UPDRS']]

class ImagingOnlyDataExperiment(DataExperiment):
    key = "dmri"

    def filter_data(self, data):
        standard_data = get_standardized_data(data)
        return standard_data.drop(['UPDRS'], axis=1)

class FullDataExperiment(DataExperiment):
    key = "both"

    def filter_data(self, data):
        return get_standardized_data(data)


def get_standardized_data(data):
    # TODO: Find a cleaner way to do this
    columns_conf = pathlib.Path(__file__).parent.parent.parent / 'resources/column_names.conf'
    with open(str(columns_conf)) as f:
        columns = f.read().splitlines() 
        return data[columns]
