import warnings
import os

# from ui.user_input import get_prediction
warnings.filterwarnings("ignore") 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# import libraries and files
from termcolor import colored
from imblearn.over_sampling import RandomOverSampler
import numpy as np
from tensorflow.keras.models import load_model # type: ignore
from sklearn.model_selection import train_test_split
from src.ui.colors import get_acc_color, get_loss_color
from src.prep_data.get_df import build_dataframe
from src.prep_data.preprocess import load_data
from src.audio_classifier.build_model import create_classifier, train_classifier
from src.ui.cleanup import final_cleanup
from sklearn.metrics import accuracy_score
from src.prep_data.evaluate_dataset import plot_dataset
from src.ui.visualization import visualize_stats, plot_confusion_matrix
from tf_lite_utils.tflite_utils import compare_models, load_lite_model, lite_inference
from tf_lite_utils.converter.tflite_converter import convert_for_microcontroller, get_representative_dataset

# force gpu usage
# assert tf.config.list_physical_devices('GPU'), "No GPU available. Exiting."

# directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # path to vocalization_classifier/
MODEL_DIR = os.path.join(BASE_DIR, "models")

FULL_MODEL_PATH = os.path.join(MODEL_DIR, "BarkBeacon_Full.h5")
LITE_MODEL_PATH = os.path.join(MODEL_DIR, "BarkBeacon_Lite.tflite")
AUDIO_ROOT_PATH = '../dataset/combined'


# config variables
valid_split = 0.1 # % of dataset to use for validation 
BATCH_SIZE = 16 # num of files per sample 
SAMPLE_RATE = 16000 # sample rate to downsample to
DURATION_SEC = 4 # time length of audio file (seconds)
NUM_EPOCHS = 100

# check_gpu() # check if gpu is being used

df = build_dataframe(AUDIO_ROOT_PATH)
# plot_dataset(df)

# split dataset
train_data, val_data = train_test_split(df, test_size=valid_split, stratify=df['classID'], random_state=42)
label_names = sorted(df['class'].unique())
num_classes = len(label_names) # get total number of classes

# preprocess/load the data
train_features, train_labels = load_data(AUDIO_ROOT_PATH, train_data, SAMPLE_RATE, DURATION_SEC, df_type="training")
val_features, val_labels = load_data(AUDIO_ROOT_PATH, val_data, SAMPLE_RATE, DURATION_SEC, df_type="validation")

# oversample to help with class imbalance
ros = RandomOverSampler(random_state=42)
train_features, train_labels = ros.fit_resample(train_features, train_labels)

audio_classifier = create_classifier(num_classes)
classifier_history = train_classifier(audio_classifier, train_features, train_labels, val_features, val_labels, NUM_EPOCHS, BATCH_SIZE)

# save full model to h5 file
audio_classifier.save(FULL_MODEL_PATH)

# compare model accuracy
compare_models(val_features, val_labels, FULL_MODEL_PATH, LITE_MODEL_PATH)

# # plot training results
# plot_confusion_matrix(audio_classifier, val_features, val_labels, label_names) # create confusion matrix
# visualize_stats(classifier_history) # visualize the loss/acc

# TODO: fix prediction to test custom files
# get_prediction(audio_classifier, SAMPLE_RATE, DURATION_SEC, label_names, train_features, AUDIO_ROOT_PATH)

final_cleanup()
print("Exiting...")
