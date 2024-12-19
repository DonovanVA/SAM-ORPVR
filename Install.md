# Updated ORPVR Installation and Usage Guide
Hi as you all know the original ORPVR by https://github.com/jinjungyu/ORPVR has been outdated and does not have any version checking so this repo will help to find and explain the required libraries (and versions) especially those facing issues with mmcv and mmdet

##### Research paper:
##### J. -G. Jin, J. Bae, H. -G. Baek and S. -H. Park, "Object-Ratio-Preserving Video Retargeting Framework based on Segmentation and Inpainting," 2023 IEEE/CVF Winter Conference on Applications of Computer Vision Workshops (WACVW), Waikoloa,HI, USA, 2023, pp. 497-503, doi: 10.1109/WACVW58289.2023.00055.

## Notes/Precautions:
#### After hours of finding the correct version, I discovered these key changes and important precautions to take when installing:
1. You cannot use `mmcv>=2.0.0` as the new configuration lacks the appropriate models and dependencies that are needed for ORPVR
2. Do not install `mmdet` independently as it will also force install the later or compatible version of mmcv 
3. You have to `pip install -v -e .` from the mmdetection 2.x, as I will explain later
4. Tensorflow does not have support for the later cuda versions (12.x), so it is best to install (11.x)
5. Missing dll files can be identified and downloaded
6. Crop step was missing from the repo, so I added `crop.py` to crop the images from DAVIS 2016 as mentioned in their paper before running the pipeline: 
    - Original repo: masking->inpainting->relocating->encoding
    - This repo: crop->masking->inpainting->relocating->encoding
7. AOT-GAN has a poorer performance as mentioned in the paper, but it can be selected and used.
8. If you are using GPU, install the relvant python GPU torch libraries (Step 1 in Setting up Guide) BEFORE installing mmcv-full, or else you will install the mmcv-full CPU version.
`e2fgvi_hq` should only be used as the model, other models are not as effective, and `dynamic` should be used (mode 2) for the relocating
Video Output:

https://github.com/user-attachments/assets/ba2d2ad6-ed55-43d9-bd63-faac7083846a


### Setting Up Guide
Navigate to the `src` directory
I use windows using python 3.9.x, but you can also set up a docker container if it is more manageable. Also, if you are using GPU. Remember to do step 1 first then step 2.

1. **Install the correct CUDA version (I am using 11.7)**

    ### CUDAv11.7
    - CUDA https://developer.nvidia.com/cuda-toolkit
    - check your CUDA_PATH using something like echo %CUDA_PATH% or if you are using windows like me, check using edit the system environment variables -> Advanced -> Environment Variables and then you should see:

    ![Screenshot 2024-09-21 231625](https://github.com/user-attachments/assets/26b4d499-afd6-4c33-b2c2-fd7a6d5160fd)
    under system variables, if not add a new CUDA_PATH and CUDA_PATH_V11_7 
    - Create a new conda environment (python 3.9.x)
    ```bash
    conda create -n SAM-ORPVR python=3.9
    ```
    
    - (For windows): If you are unable to switch the CUDA environment freely or see the conda version `(SAM-ORPVR) PS C:\Users\User...>`, run the following command below as `administrator`
    ```bash
    Set-ExecutionPolicy RemoteSigned
    ```
    
    - Activate the new environment
    ```bash
    conda activate SAM-ORPVR
    ```

    - Install correct python torch CUDA-enabled libraries for CUDA, run the commands here: (https://pytorch.org/get-started/previous-versions/)
    ```bash
    conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia
    ```

    - ^ if the above does not work and you still get a CUDA error run
    ```bash
    pip uninstall torch torchvision torchaudio
    ```
    then
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
    ```

    - after installing tensorflow and CUDA-enabled torch, you should get these versions:
    ```bash
    torch                         2.0.1+cu117
    torchaudio                    2.0.2+cu117
    torchvision                   0.15.2+cu117
    ```

    run the following code to check cuda:
    ```bash
    python cudacheck.py
    ```
    
    you should get this:
    ```bash
    torch GPU check:
    True
    GPU:NVIDIA GeForce RTX 3070
    ```

    - then add in the appropriate dll files if not found (for me it was cudnn64_8.dll not found):
    https://www.dll-files.com/cudnn64_8.dll.html#google_vignette
    place it in the
    NVIDIA GPU Computing Toolkit\CUDA\v11.7\bin

    check CUDA using this command:
    ```bash
    nvcc --version
    ```

    You should get:
    ```bash
    nvcc: NVIDIA (R) Cuda compiler driver
    Copyright (c) 2005-2022 NVIDIA Corporation
    Built on Tue_May__3_19:00:59_Pacific_Daylight_Time_2022
    Cuda compilation tools, release 11.7, V11.7.64
    Build cuda_11.7.r11.7/compiler.31294372_0
    ```
    - download `util` file in `test clear` commit of main branch (ORPVR SHA eef6dcb39e05041e044e46141db80d37fb93d9b4)
      https://github.com/jinjungyu/ORPVR/tree/main (I included here so you dont have to)

    ### CPU only
    - If you want the cpu version only then do:
    ```bash
     pip install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0
    ```

2. **Install Dependencies and DAVIS 2016 dataset (Order is important, FOLLOW carefully):**

    - Install openmim
    ```bash
    pip install -U openmim
    mim install mmcv-full
    ```

    - Davis Dataset: https://davischallenge.org/davis2016/code.html

    - Download mmdetection v2.0
    https://github.com/open-mmlab/mmdetection/tree/2.x

    ```bash
    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    *WARNING: DO NOT install mmcv==1.7.2 and the latest version (2.0.0+) as it will lead to keyErrors mmcv.runner and mmcv._ext module not found

    Ensure you have the following versions of the packages:
   - `mmcv-full` 1.7.2
   - `mmdet` 2.28.2
   - `mmengine` 0.10.4

   *If you accidentally install the wrong version (probably if you install mmdetection 3.x+), uninstall the current packages and reinstall:

    ```bash
    pip uninstall mmdet
    pip uninstall mmcv
    pip uninstall mmcv-full
    pip install -U openmim
    mim install mmcv-full

    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    then make sure you are using mmdetection v2.0:
    https://github.com/open-mmlab/mmdetection/tree/2.x
    before running 
    
    ```bash
    cd mmdetection
    mkdir checkpoints
    pip install -v -e .
    ```
    again

    then install the necessary libraries:
    ```bash
    pip install -r requirements.txt
    ```


3. **mask2former Model**

    - Download mask2former model and put inside `mmdetection/checkpoints` (branch 2.0): https://github.com/open-mmlab/mmdetection/blob/2.x/configs/mask2former/README.md

4. **SAM Model**

    ```bash
    mkdir SAM
    cd SAM
    mkdir checkpoints
    ```
    - Install segment anything

    ```bash
    pip install git+https://github.com/facebookresearch/segment-anything.git
    ```

    - Download SAM model and put inside `SAM/checkpoints` : https://github.com/facebookresearch/segment-anything?tab=readme-ov-file#model-checkpoints
    *I am using `vit_h`, options are `vit_h`,`vit_l`,`vit_b`
    Note: Requires device spec

    SAM2:
    * Install SAM2
    ```bash
    git clone https://github.com/facebookresearch/sam2.git
    cd sam2
    ```

    * Also, we use python `3.9.x` here because it works with E2FGVI and mask2former (the previous set up), the 3.10.x suggested by Meta is only for accelerated computing
    https://github.com/facebookresearch/sam2/blob/main/INSTALL.md

    * The error below occurs if you dont have desktop environment for C++ installed (recommend to install it through microsoft visual studio)
    ```bash
    C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.38.33130/include\crtdefs.h(10): fatal error C1083: Cannot open include file: 'corecrt.h': No such file or directory
command 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v11.7\\bin\\nvcc.exe' failed with exit code 2
    ```

5. **Inpainting Model**

    For inpainting, we will standardise to `E2FGVI` as it is stated to be more accurate by the research paper
    In main directory, Install `E2FGVI` and `AOT-GAN-for-Inpainting`:
    ```bash
    git clone https://github.com/MCG-NKU/E2FGVI.git
    ```
    - Install the model https://drive.google.com/file/d/10wGdKSUOie0XmCr8SQ2A2FeDe-mfn5w3/view
    put the model in /release_model

    - Download the weights G0000000.pt:
    https://drive.google.com/drive/folders/1bSOH-2nB3feFRyDEmiX81CEiWkghss3i
    and place it in AOT-GAN-for-Inpainting/experiments/

    - Install the other inpainting model (video), it is optional:
    git clone https://github.com/hyunobae/AOT-GAN-for-Inpainting.git

6. **masking.py fix (if you get AssertionError)**

    change this in line 11
    ```python
    from mmdetection.mmdet.apis import inference_detector,init_detector
    with mmdet.apis import inference_detector,init_detector
    ```