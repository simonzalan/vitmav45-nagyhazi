# -*- coding: utf-8 -*-
"""VItmav45 Nagyhazi 2. milestone.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LXPOJqc4pwYx3vkcV_MGtOrDSj4hAwBg

Getting image datasets from the MVTEC website
"""
from tensorflow.python.client import device_lib

print(device_lib.list_local_devices())

import os
os.mkdir("/content")
os.chdir("/content")
os.system("wget https://www.mydrive.ch/shares/38536/3830184030e49fe74747669442f0f282/download/420938113-1629952094/mvtec_anomaly_detection.tar.xz -O mvtec_anomaly_detection.tar.xz")
os.system("tar -xf mvtec_anomaly_detection.tar.xz")

os.system("ls /content/")
os.system("ls /")

"""Installing library for easy splitting of the downloaded dataset"""

os.system("pip install split-folders")

"""Creating a validation image batch from the training batch"""

import splitfolders
splitfolders.ratio("/content/hazelnut/train", output="output1", seed=1337, ratio=(.9,0.1))

"""Checking if the images are in their places"""

os.system("ls /content/output1/train/good")

"""Testing if the images are where they need to be"""

from IPython.display import Image
Image("/content/output1/val/good/009.png")

"""Importing libraries that will be used later"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import os
from PIL import Image
import matplotlib.pyplot as plt
import random

# %matplotlib inline

from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Dropout, Flatten, GlobalAveragePooling2D, UpSampling2D
from tensorflow.keras.utils import to_categorical, image_dataset_from_directory
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing.image import ImageDataGenerator

"""Loading the images into variables(training, testinf and validation)"""

image_size = 128
batch_size = 64

datagen = ImageDataGenerator(rescale=1./255)
train_generator = datagen.flow_from_directory(
    '/content/output1/train/',
    target_size=(image_size, image_size),
    batch_size=batch_size,
    class_mode='input'
    )

validation_generator = datagen.flow_from_directory(
    '/content/output1/val/',
    target_size=(image_size, image_size),
    batch_size=batch_size,
    class_mode='input'
    )

anomaly_generator = datagen.flow_from_directory(
    '/content/carpet/test/',
    target_size=(image_size, image_size),
    batch_size=batch_size,
    class_mode='input'
    )

train_ds = image_dataset_from_directory("/content/output1/train/", 
                                        label_mode='categorical',
                                        image_size=(image_size, image_size),
                                        batch_size=batch_size)
val_ds = image_dataset_from_directory("/content/output1/val/",
                                      label_mode='categorical',
                                      image_size=(image_size, image_size),
                                      batch_size=batch_size)
test_ds = image_dataset_from_directory("/content/carpet/test/",
                                      label_mode='categorical',
                                      image_size=(image_size, image_size),
                                      batch_size=batch_size)

"""Checking if the images are all the same size"""

from PIL import Image
import os.path

files = os.listdir("/content/output1/val/good/")
same_size = True
for f in files:
    filename = "/content/output1/val/good/" + f
    im = Image.open(filename)
    #print(im.size)
    if im.size != (1024, 1024):
        print("NOT OK")
        same_size = False

print(same_size)
print(train_ds.snapshot)

"""Encoder and Decoder

"""

#Encoder
model = Sequential()
model.add(Conv2D(64, (3, 3), activation='relu', padding='same', input_shape=(image_size, image_size, 3)))
model.add(MaxPooling2D((2, 2), padding='same'))
model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
model.add(MaxPooling2D((2, 2), padding='same'))
model.add(Conv2D(16, (3, 3), activation='relu', padding='same'))
model.add(MaxPooling2D((2, 2), padding='same'))

#Decoder
model.add(Conv2D(16, (3, 3), activation='relu', padding='same'))
model.add(UpSampling2D((2, 2)))
model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
model.add(UpSampling2D((2, 2)))
model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
model.add(UpSampling2D((2, 2)))

model.add(Conv2D(3, (3, 3), activation='sigmoid', padding='same'))

model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mse'])
model.summary()

"""Fitting the model"""

history = model.fit(
        train_generator,
        steps_per_epoch= 300 // batch_size,
        epochs=100,
        validation_data=validation_generator,
        validation_steps=75 // batch_size,
        shuffle = True)

"""Plot the training and validation accuracy and loss at each epoch"""

loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

"""Get all batches generated by the datagen and pick a batch for prediction"""

data_batch = []
img_num = 0
while img_num <= train_generator.batch_index:   
    data = train_generator.next()
    data_batch.append(data[0])
    img_num = img_num + 1

predicted = model.predict(data_batch[0])

"""View few images and corresponding reconstructions"""

image_number = random.randint(0, predicted.shape[0])
plt.figure(figsize=(12, 6))
plt.subplot(121)
plt.imshow(data_batch[0][image_number])
plt.subplot(122)
plt.imshow(predicted[image_number])
plt.show()

"""Examine the reconstruction error between our validation data (good/normal images) and the anomaly images"""

validation_error = model.evaluate_generator(validation_generator)
anomaly_error = model.evaluate_generator(anomaly_generator)

print("Recon. error for the validation (normal) data is: ", validation_error)
print("Recon. error for the anomaly data is: ", anomaly_error)

"""Let us extract (or build) the encoder network, with trained weights.This is used to get the compressed output (latent space) of the input image. The compressed output is then used to calculate the KDE"""

encoder_model = Sequential()
encoder_model.add(Conv2D(64, (3, 3), activation='relu', padding='same', input_shape=(image_size, image_size, 3), weights=model.layers[0].get_weights()) )
encoder_model.add(MaxPooling2D((2, 2), padding='same'))
encoder_model.add(Conv2D(32, (3, 3), activation='relu', padding='same', weights=model.layers[2].get_weights()))
encoder_model.add(MaxPooling2D((2, 2), padding='same'))
encoder_model.add(Conv2D(16, (3, 3), activation='relu', padding='same', weights=model.layers[4].get_weights()))
encoder_model.add(MaxPooling2D((2, 2), padding='same'))
encoder_model.summary()

# Calculate KDE using sklearn
from sklearn.neighbors import KernelDensity

#Get encoded output of input images = Latent space
encoded_images = encoder_model.predict_generator(train_generator)

# Flatten the encoder output because KDE from sklearn takes 1D vectors as input
encoder_output_shape = encoder_model.output_shape #Here, we have 16x16x16
out_vector_shape = encoder_output_shape[1]*encoder_output_shape[2]*encoder_output_shape[3]

encoded_images_vector = [np.reshape(img, (out_vector_shape)) for img in encoded_images]

#Fit KDE to the image latent data
kde = KernelDensity(kernel='gaussian', bandwidth=0.2).fit(encoded_images_vector)

"""Calculate density and reconstruction error to find their means values forgood and anomaly images. We use these mean and sigma to set thresholds. """

def calc_density_and_recon_error(batch_images):
    
    density_list=[]
    recon_error_list=[]
    for im in range(0, batch_images.shape[0]-1):
        
        img  = batch_images[im]
        img = img[np.newaxis, :,:,:]
        encoded_img = encoder_model.predict([[img]]) 
        encoded_img = [np.reshape(img, (out_vector_shape)) for img in encoded_img] 
        density = kde.score_samples(encoded_img)[0] 
        reconstruction = model.predict([[img]])
        reconstruction_error = model.evaluate([reconstruction],[[img]], batch_size = 1)[0]
        density_list.append(density)
        recon_error_list.append(reconstruction_error)
        
    average_density = np.mean(np.array(density_list))  
    stdev_density = np.std(np.array(density_list)) 
    
    average_recon_error = np.mean(np.array(recon_error_list))  
    stdev_recon_error = np.std(np.array(recon_error_list)) 
    
    return average_density, stdev_density, average_recon_error, stdev_recon_error

"""Get average and std dev. of density and recon. error for uninfected and anomaly (parasited) images. 
For this let us generate a batch of images for each. 
"""

train_batch = train_generator.next()[0]
anomaly_batch = anomaly_generator.next()[0]

uninfected_values = calc_density_and_recon_error(train_batch)
anomaly_values = calc_density_and_recon_error(anomaly_batch)

import PIL

"""Input unknown images and sort as Good or Anomaly"""

def check_anomaly(img_path):
    density_threshold = 2500 
    reconstruction_error_threshold = 0.004 
    img  = PIL.Image.open(img_path)
    img = np.array(img.resize((128,128), PIL.Image.ANTIALIAS))
    plt.imshow(img)
    img = img / 255.
    img = img[np.newaxis, :,:,:]
    encoded_img = encoder_model.predict([[img]]) 
    encoded_img = [np.reshape(img, (out_vector_shape)) for img in encoded_img] 
    density = kde.score_samples(encoded_img)[0] 

    reconstruction = model.predict([[img]])
    reconstruction_error = model.evaluate([reconstruction],[[img]], batch_size = 1)[0]

    if density < density_threshold or reconstruction_error > reconstruction_error_threshold:
        print("The image is an anomaly")
        
    else:
        print("The image is NOT an anomaly")

"""Load a couple of test images and verify whether they are reported as anomalies"""

import glob
para_file_paths = glob.glob('/content/hazelnut/test/hole/*')
uninfected_file_paths = glob.glob('/content/hazelnut/test/good/*')

"""Anomaly image verification"""

num=random.randint(0,len(para_file_paths)-1)
check_anomaly(para_file_paths[num])

"""Good/normal image verification"""

num=random.randint(0,len(para_file_paths)-1)
check_anomaly(uninfected_file_paths[num])

