
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report, f1_score, accuracy_score,recall_score,precision_score
from sklearn.model_selection import train_test_split


import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

import cv2


data_dir = 'images'
images = os.listdir(data_dir)


test_images = pd.read_csv('CXR8/test_list.txt', header=None)


test_images

train_images = pd.read_csv('CXR8/train_val_list.txt', header=None)

train_images

labels = pd.read_csv('CXR8/Data_Entry_2017_v2020.csv')



all_labels = '|'.join(labels['Finding Labels'].unique())
all_labels = all_labels.split('|')
all_labels = list(set(all_labels))



for label in all_labels:
    labels[label] = labels['Finding Labels'].apply(lambda x: 1 if label in x else 0)


labels


tenso = torch.tensor(labels[all_labels].values).float()
data = pd.DataFrame()
data['Image Index'] = labels['Image Index']
data[all_labels] = tenso


data = data.drop(columns=['No Finding'])


all_labels

all_labels_without_no_finding = all_labels.copy()
all_labels_without_no_finding.remove('No Finding')
all_labels_without_no_finding

from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image


class CXR8Dataset(Dataset):
    def __init__(self, data, data_dir, transform=None):
        super().__init__()
        self.data = data
        self.data_dir = data_dir
        self.transform = transform

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        img_name = self.data.iloc[index, 0]
        img_path = os.path.join(self.data_dir, img_name)
        image = Image.open(img_path).convert('RGB')

        if self.transform is not None:
            image = self.transform(image)
        label = self.data.iloc[index, 1:].values
        label = np.array(label, dtype=np.float32)
        label = torch.tensor(label, dtype=torch.float32)

        return image, label
# create a transform

train_transform = transforms.Compose([
    #transforms.ToPILImage(),
 #   transforms.Grayscale(num_output_channels=1),  # Convert to grayscale
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.2),
    transforms.ToTensor()
])

val_transform = transforms.Compose([
    #transforms.ToPILImage(),
  #  transforms.Grayscale(num_output_channels=1),  # Convert to grayscale
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

if __name__ == '__main__':

    data = data[:50000]

    train_data, val_data = train_test_split(data, test_size=0.2, random_state=42)



    train_dataset = CXR8Dataset(train_data, data_dir, train_transform)
    val_dataset = CXR8Dataset(val_data, data_dir, val_transform)

    # create a dataloader
    train_loader = DataLoader(
        train_dataset,
        batch_size=64,
        shuffle=True,
        num_workers=10,  # Run single-threaded to identify issues
        pin_memory=True
    )

    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)



    import torchvision.models as models 
    from torchvision.models.resnet import ResNet, BasicBlock
    from torchvision.models.resnet import ResNet50_Weights
    model = models.resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)

    model.fc = nn.Sequential(
        nn.Linear(2048, 1024),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(1024, 512),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(512, 14)
    )



    for param in model.parameters():
        param.requires_grad = False

    for param in model.fc.parameters():
        param.requires_grad = True
    # define the loss and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # train the model
    num_epochs = 10
    train_losses = []
    val_losses = []




    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    device
    print(device)

    model.to(device)
    for epoch in range(num_epochs):
        
        train_loss = 0.0
        val_loss = 0.0
        
        model.train()
        for images, labels in train_loader:
            
        
            images, labels = images.to(device), labels.to(device)


            
        
            optimizer.zero_grad()
            output = model(images)
        
            loss = criterion(output, labels.float())
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
            
        model.eval()
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            output = model(images)
            loss = criterion(output, labels.float())
            val_loss += loss.item()
            
        train_losses.append(train_loss/len(train_loader))
        val_losses.append(val_loss/len(val_loader))

        
        print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss/len(train_loader)}, Val Loss: {val_loss/len(val_loader)}')


    model.eval()
    predictions = []
    actuals = []

    for images, labels in val_loader:
        images, labels = images.to(device), labels.to(device)
        output = model(images)
        output = torch.sigmoid(output)
        output = output.cpu().detach().numpy()
        predictions.extend(output)
        actuals.extend(labels.cpu().detach().numpy())

    predictions = np.array(predictions)
    actuals = np.array(actuals)

    predictions = np.where(predictions > 0.5, 1, 0)

    accuracy = accuracy_score(actuals, predictions)
    recall = recall_score(actuals, predictions, average='micro')
    precision = precision_score(actuals, predictions, average='micro')
    f1 = f1_score(actuals, predictions, average='micro')


    print(classification_report(actuals, predictions, target_names=all_labels_without_no_finding, zero_division=0))


    accuracy, recall, precision, f1

    print('Accuracy:', accuracy)
    print('Recall:', recall)
    print('Precision:', precision)
    print('F1 Score:', f1)


    from sklearn.metrics import roc_auc_score
    roc_auc_score(actuals, predictions)

    print('ROC AUC Score:', roc_auc_score(actuals, predictions))



