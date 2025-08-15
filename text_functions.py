import torch
from transformers import BertTokenizer, BertModel
import gc
import numpy as np


num_2_text = {0: 'agriculture',
              1: 'alcohol',
              2: 'arts_and_culture',
              3: 'commercial',
              4: 'parked_domain',
              5: 'sexual_service',
              6: 'porn'}

text_2_num = {'agriculture': 0,
              'alcohol': 1,
              'arts_and_culture': 2,
              'commercial': 3,
              'parked_domain': 4,
              'sexual_service': 5,
              'porn': 6}


# Load pre-trained model and tokenizer
tokenizer = BertTokenizer.from_pretrained( "bert-base-uncased" )
text_model = BertModel.from_pretrained( "bert-base-uncased" )

# Move model to GPUs for model parallelism
device = torch.device("cuda:2")

# Split the model across 3 GPUs
text_model = text_model.to(device)  # First part of the model on GPU 0


def text_embeddings( sample_id ):
    
    text_path = f"./static/screenshots/{sample_id}.txt"
    with open( text_path ) as f:
        website_text = f.read()

    #just use first 20k characters for predictions
    website_text = website_text[:20000]

    # Prepare a batch (this will be on GPU 1)
    inputs = tokenizer( [website_text] , return_tensors="pt", padding=True, truncation=True)
    
    # Move inputs to the appropriate GPU|                                         |                        |                  N/A |

    inputs = {key: value.to(device) for key, value in inputs.items()}

    # Get embeddings from BERT
    with torch.no_grad():
        # Forward pass through the model on GPU 1
        outputs = text_model(**inputs)
        
        # Extract the last hidden states
        last_hidden_states = outputs.last_hidden_state

        # Compute the embeddings (average the token embeddings for the sentence representation)
        sentence_embedding = last_hidden_states.mean(dim=1)
        
        # Use the [CLS] token embedding
        cls_embedding = last_hidden_states[:, 0, :]

    # Move all embeddings to the target device before appending them to the list
    sentence_embedding = sentence_embedding.to(device).cpu().tolist()
    cls_embedding = cls_embedding.to(device).cpu().tolist()


    # Clean up
    del outputs
    del inputs
    del last_hidden_states

    # Optionally run garbage collection
    gc.collect()

    # Clear unused memory on GPU
    torch.cuda.empty_cache()

    return sentence_embedding , cls_embedding


from transformers import Blip2ForConditionalGeneration, AutoProcessor
import torch
from PIL import Image

image_model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b").to(device)
image_processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")


def image_embeddings ( sample_id ):
    image_paths = [ f"./static/screenshots/{sample_id}.png" ]
    
    # Load all images into a list
    images = [Image.open(path).convert("RGB") for path in image_paths]
    
    # Process images as a batch
    inputs = image_processor(images=images, return_tensors="pt").to(device)  # Batch dimension added here
    
    # =============================================
    # 2. Batch Processing for CLIP Features
    # =============================================
    with torch.no_grad():
        vision_outputs = image_model.vision_model(**inputs)
    
    # Get CLS tokens for all images in batch
    batch_image_features = vision_outputs.last_hidden_state[:, 0, :]  # Shape: [100, hidden_size]
    batch_image_features_np = batch_image_features.cpu().numpy()  
    
    CLIP_features = [ list(arr) for arr in batch_image_features_np ]
    
    # =============================================
    # 3. Batch Processing for Q-Former Features
    # =============================================
    image_embeds = vision_outputs.last_hidden_state  # Already batched
    
    # Expand query tokens to match batch size
    query_tokens = image_model.query_tokens.expand(image_embeds.shape[0], -1, -1)  # [100, 32, hidden_size]
    
    with torch.no_grad():
        qformer_outputs = image_model.qformer(
            query_embeds=query_tokens,
            encoder_hidden_states=image_embeds,
            return_dict=True
        )
    
    # Get pooled features for all 100 images
    batch_qformer_features = qformer_outputs.last_hidden_state.mean(dim=1)  # Shape: [100, hidden_size]
    
    # Convert to numpy (optional)
    batch_features_np = batch_qformer_features.cpu().numpy()

    qformer_features = [ list(arr) for arr in batch_features_np ]
    
    # Cleanup: Delete intermediate variables
    del image_paths, images, inputs, vision_outputs, batch_image_features, batch_image_features_np
    del image_embeds, query_tokens, qformer_outputs, batch_qformer_features, batch_features_np
    
    torch.cuda.empty_cache()  # Clear PyTorch's GPU cache
    gc.collect()  # Force Python garbage collection

    return CLIP_features, qformer_features





from torch.utils.data import Dataset, DataLoader
import torch.nn as nn


# Define dataset class with verification
class MultimodalDataset(Dataset):
    def __init__(self, X1, X2):
        assert len(X1) == len(X2)
        
        self.X1 = X1
        self.X2 = X2
        
        assert self.X1.dim() == 2, "X1 must be 2D (samples, features)"
        assert self.X2.dim() == 2, "X2 must be 2D (samples, features)"

    def __len__(self):
        return len(self.X1)

    def __getitem__(self, idx):
        return (self.X1[idx], self.X2[idx])


# Define model architecture
class MultiheadAttentionModel(nn.Module):
    def __init__(self, dim1=768, dim2=1408, num_classes=7, d_model=256, num_heads=8, dropout_rate=0.2):
        super().__init__()
        self.proj1 = nn.Sequential(
            nn.Linear(dim1, d_model),
            nn.BatchNorm1d(d_model),
            nn.Dropout(0.3)
        )
        self.proj2 = nn.Sequential(
            nn.Linear(dim2, d_model),
            nn.BatchNorm1d(d_model),
            nn.Dropout(0.3)
        )
        self.attention = nn.MultiheadAttention(embed_dim=d_model, num_heads=num_heads, dropout=dropout_rate)
        self.classifier = nn.Sequential(
            nn.Linear(d_model * 2, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, num_classes)
        )

    def forward(self, x1, x2):
        x1_proj = self.proj1(x1).unsqueeze(1)
        x2_proj = self.proj2(x2).unsqueeze(1)
        combined = torch.cat([x1_proj, x2_proj], dim=1).permute(1, 0, 2)
        attn_output, _ = self.attention(combined, combined, combined)
        aggregated = attn_output.mean(dim=0)
        residual = (x1_proj + x2_proj).squeeze(1)
        combined = torch.cat([aggregated, residual], dim=1)
        return self.classifier(combined)



# Custom collate function for safety
def collate_fn(batch):
    x1 = torch.stack([item[0] for item in batch])
    x2 = torch.stack([item[1] for item in batch])
    return (x1, x2)
    

model_save_path = "./models/attention.pth"
attention_model = torch.load(model_save_path, map_location=device, weights_only=False)
attention_model.eval()  # Set model to evaluation mode


def predict( sample_id ):

    sentence_embedding , cls_embedding = text_embeddings( sample_id )
    CLIP_features, qformer_features = image_embeddings ( sample_id )

    # Assume X1_test, X2_test are your test data and are numpy arrays or tensors
    # If your data is in numpy arrays, convert them to tensors
    
    X1_test = torch.tensor( sentence_embedding , dtype=torch.float32).clone().detach()
    X2_test = torch.tensor( CLIP_features , dtype=torch.float32).clone().detach()
    
    
    # Create a dataset and DataLoader for the test data
    test_dataset = MultimodalDataset(X1_test, X2_test)  # No labels in the dataset for prediction
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
        

    predictions = []
    with torch.no_grad():  # No need to track gradients during inference
        for x1, x2, in test_loader:
            x1, x2 = x1.to(device), x2.to(device)
            outputs = attention_model(x1, x2)
            _, predicted = torch.max(outputs, 1)  # Get the index of the class with the highest probability
            predictions.extend(predicted.cpu().numpy())  # Move predictions to CPU and convert to numpy

    predictions =  np.array(predictions)

    return num_2_text[ predictions[0]  ]
    
# predict( "8212b19d-ff45-44a5-9bb0-006fced88ebc"  )