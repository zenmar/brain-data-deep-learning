from tensorflow.keras.utils import Sequence
import h5py
from sklearn.utils import shuffle
import numpy as np
import gc
import data_utils as utils
import tensorflow as tf

class Generator(Sequence):
    def __init__(self, files_paths, ram_to_use, data_type,using_gpu): #ram_to_use in GB
        self.files_paths = files_paths
        # self.batch_size = batch_size
        self.index_batch = 0
        self.index_batch_files = 0
        self.ram_to_use = ram_to_use #not used anymore because unknown memory management of TF2 with/without GPU/CPU
        self.data_type = data_type # will be train or validate or test
        self.using_gpu = using_gpu
        self.number_files = self.get_number_files_to_load()
        
        

    def get_number_files_to_load(self):
        if self.using_gpu:
            number_files = 2            
        else:
            number_files = 6

        return number_files

    def get_dataset_name(self,file_name_with_dir):
        filename_without_dir = file_name_with_dir.split('/')[-1]
        temp = filename_without_dir.split('_')[:-1]
        dataset_name = "_".join(temp)
        return dataset_name


    def load_data(self):
#        print("data type: {}\nindex_batch_files: {}\nnumber_files: {}".format(self.data_type,self.index_batch_files,self.number_files))
        rest_matrix = np .zeros((248,1))
        task_matrix = np .zeros((248,1))

        files_to_load = self.files_paths[self.index_batch_files * self.number_files: (self.index_batch_files + 1) * self.number_files]

        for i in range(len(files_to_load)):
            if "rest" in files_to_load[i]:
                with h5py.File(files_to_load[i],'r') as f:
                    dataset_name = self.get_dataset_name(files_to_load[i])
                    matrix = f.get(dataset_name)
                    matrix = np.array(matrix)
                assert matrix.shape[0] == 248 , "This rest data does not have 248 channels, but {} instead".format(matrix.shape[0])
                rest_matrix = np.column_stack((rest_matrix, matrix))

            if "task" in files_to_load[i]:
                with h5py.File(files_to_load[i],'r') as f:
                    dataset_name = self.get_dataset_name(files_to_load[i])
                    matrix = f.get(dataset_name)
                    matrix = np.array(matrix)
                assert matrix.shape[0] == 248 , "This task data does not have 248 channels, but {} instead".format(matrix.shape[0])
                task_matrix = np.column_stack((task_matrix, matrix))

        rest_matrix = np.delete(rest_matrix, 0, 1)#delete first column made of 0s
        task_matrix = np.delete(task_matrix, 0, 1)#delete first column made of 0s
        if (rest_matrix.shape[1] != 0):
            rest_is_empty = False
#            print("rest matrix shape",rest_matrix.shape)
            rest_matrix = self.normalize_matrix(rest_matrix)
            rest_length = utils.closestNumber(int(rest_matrix.shape[1]) - 10,10)
            rest_meshes = np.zeros((rest_length,20,22))
            for i in range(rest_length):
                array_time_step = np.reshape(rest_matrix[:,i],(1,248))
                rest_meshes[i] = utils.array_to_mesh(array_time_step)

            del rest_matrix
            gc.collect()
            input1_rest,input2_rest,input3_rest,input4_rest,input5_rest = self.get_input_lists(rest_meshes, self.get_lists_indexes(rest_length))
            del rest_meshes
            gc.collect()
            number_y_labels_rest = int(rest_length/5)
            y_rest = np.zeros((number_y_labels_rest,1),dtype=np.int8)
        else:
            rest_is_empty = True

        if (task_matrix.shape[1] != 0):
            task_is_empty = False
#            print("task matrix shape",task_matrix.shape)
            task_matrix = self.normalize_matrix(task_matrix)           
            task_length = utils.closestNumber(int(task_matrix.shape[1]) - 10,10)
            task_meshes = np.zeros((task_length,20,22))
            for i in range(task_length):
                array_time_step = np.reshape(task_matrix[:,i],(1,248))
                task_meshes[i] = utils.array_to_mesh(array_time_step)

            del task_matrix
            gc.collect()
            input1_task,input2_task,input3_task,input4_task,input5_task = self.get_input_lists(task_meshes, self.get_lists_indexes(task_length))
            del task_meshes
            gc.collect()
            number_y_labels_task = int(task_length/5)
            y_task = np.ones((number_y_labels_task,1),dtype=np.int8)
        else:
            task_is_empty = True


        if(not rest_is_empty and not task_is_empty):
            input1 = np.concatenate((input1_rest,input1_task))
            input2 = np.concatenate((input2_rest,input2_task))
            input3 = np.concatenate((input3_rest,input3_task))
            input4 = np.concatenate((input4_rest,input4_task))
            input5 = np.concatenate((input5_rest,input5_task))

            y = np.concatenate((y_rest,y_task))

            del input1_rest
            del input2_rest
            del input3_rest
            del input4_rest
            del input5_rest

            del input1_task
            del input2_task
            del input3_task
            del input4_task
            del input5_task

        elif rest_is_empty and not task_is_empty :
            input1 = input1_task
            input2 = input2_task
            input3 = input3_task
            input4 = input4_task
            input5 = input5_task
            
            y = y_task

            del input1_task
            del input2_task
            del input3_task
            del input4_task
            del input5_task

        elif task_is_empty and not rest_is_empty :
            input1 = input1_rest
            input2 = input2_rest
            input3 = input3_rest
            input4 = input4_rest
            input5 = input5_rest
            
            y = y_rest

            del input1_rest
            del input2_rest
            del input3_rest
            del input4_rest
            del input5_rest


        input1 = np.reshape(input1,(input1.shape[0],20,22,1))
        input2 = np.reshape(input2,(input2.shape[0],20,22,1))
        input3 = np.reshape(input3,(input3.shape[0],20,22,1))
        input4 = np.reshape(input4,(input4.shape[0],20,22,1))
        input5 = np.reshape(input5,(input5.shape[0],20,22,1))

        gc.collect()

        #Shuffling the data
        input1,input2,input3,input4,input5,y = shuffle(input1,input2,input3,input4,input5, y, random_state=42)

        data_dict = {'input1' : input1,'input2' : input2,'input3' : input3, 'input4': input4,'input5':input5}
        
        del input1
        del input2
        del input3
        del input4
        del input5

        gc.collect()
        
        y = tf.keras.utils.to_categorical(y,2)
        # y = tf.one_hot(y,2)

        return data_dict,y


    def normalize_matrix(self,matrix):
        max,min = matrix.max(),matrix.min()
        return (matrix-min)/(max-min)

    def get_lists_indexes(self,matrix_length):
        indexes_1 = np.arange(start=0,stop = matrix_length-4,step=5)
        indexes_2 = np.arange(start=1,stop = matrix_length-3,step=5)
        indexes_3 = np.arange(start=2,stop = matrix_length-2,step=5)
        indexes_4 = np.arange(start=3,stop = matrix_length-1,step=5)
        indexes_5 = np.arange(start=4,stop = matrix_length-0,step=5)
        return (indexes_1,indexes_2,indexes_3,indexes_4,indexes_5)
    
    def get_input_lists(self,matrix,indexes):
        inputs = []
        for i in range(5):
            inputs.append(np.take(matrix,indexes[i],axis=0))
        return inputs[0],inputs[1],inputs[2],inputs[3],inputs[4]

    def on_epoch_end(self):
        self.index_batch_files = 0

    def __len__(self): # how many batches
        return len(self.files_paths)//self.number_files
        # return math.ceil(len(self.files_paths) / self.number_files)

    def __getitem__(self, index): # returns a batch
        gc.collect()
        batch_input, batch_output = self.load_data()
        # batch_input, batch_output = self.load_synthetic_data()
        self.index_batch_files += 1
        return batch_input,batch_output
    
    def to_one_hot_binary(self, array):
        output = np.zeros((array.shape[0],2),dtype=np.int)
        for i in range(len(array)):
            if array[i] == 0:
                output[i] = np.array([1,0])
            else:
                output[i] = np.array([0,1])
        return output
    



#load X files from train and 0.5X files from validate
#from training data, prepare all 5 input lists and output list
#do the same for validate data
#approximately 1 GB in RAM = 6 train + 3 validate
#approximately 2 GB in RAM = 13 train + 6 validate
#3 GB in RAM = 20 train + 10 validate
#5GB in RAM = 33 train + 16 validate
#batch size = no longer known ( and needed )


