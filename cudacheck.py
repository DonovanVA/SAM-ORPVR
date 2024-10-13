import torch
print("torch GPU check:")
print(torch.cuda.is_available())  # Should return True if CUDA is available
if torch.cuda.is_available():
    print("GPU:"+torch.cuda.get_device_name(0))  # Prints the name of your GPU

