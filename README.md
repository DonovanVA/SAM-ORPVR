# Updated ORPVR Installation and Usage Guide
    Hi as you all know the original ORPVR by https://github.com/jinjungyu/ORPVR has been outdated and does not have any version checking so this repo will help to find and explain the required libraries (and versions) especially those facing issues with mmcv and mmdet
## Notes/Precautions:
    1. You cannot use `mmcv>=2.0.0` as the new configuration lacks the appropriate models and dependencies that are needed for ORPVR
    2. Do not install `mmdet` independently as it will also force install the later or compatible version of mmcv 
    3. You have to `pip install -v -e .` from the mmdetection 2.x, as I will explain later
    4. tensorflow does not have support for the later cuda versions (12.x), so it is best to install (11.x)
    5. Missing dll files can be identified and downloadedm
### Setting Up
    I use windows using python 3.9.x, but you can also set up a docker container if it is more manageable
    
1. **Install Dependencies and DAVIS 2016 dataset:**

    ```bash
    pip install -U openmim
    mim install mmcv-full
    ```

   - Davis Dataset: https://davischallenge.org/davis2016/code.html

2. **Download the correct version of mmdetection**
    download mmdetection v2.0
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

3. **masking.py fix (if you get AssertionError)**
    change this in line 11
    ```python
    from mmdetection.mmdet.apis import inference_detector,init_detector
    with mmdet.apis import inference_detector,init_detector
    ```
4. **download mask2former model**
    download the model and put inside mmdetection/checkpoints (branch 2.0):
    https://github.com/open-mmlab/mmdetection/blob/2.x/configs/mask2former/README.md

5. **Install the correct CUDA version (I am using 11.7x)**
    ### CUDAv11.7
    - Run the command (https://pytorch.org/get-started/previous-versions/)
    ```bash
    conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia
     ```
    
    - then add in the appropriate dll files if not found (for me it was cudnn64_8.dll not found):
        https://www.dll-files.com/cudnn64_8.dll.html#google_vignette
        place it in the
        NVIDIA GPU Computing Toolkit\CUDA\v11.7\bin
    - install tensorflow, you should get these versions:
        ```bash
        tensorflow                    2.10.1
        torch                         2.0.0
        torchvision                   0.15.0
        torchaudio                    2.0.0
        ```

    - download `util` file in `test clear` commit of main branch (ORPVR SHA eef6dcb39e05041e044e46141db80d37fb93d9b4)
      https://github.com/jinjungyu/ORPVR/tree/main

7. **inpainting.py fix:**
    ```bash
    git clone https://github.com/MCG-NKU/E2FGVI.git
    ```
    - Install the model https://drive.google.com/file/d/10wGdKSUOie0XmCr8SQ2A2FeDe-mfn5w3/view
    put the model in /release_model

    - Download the weights G0000000.pt:
    https://drive.google.com/drive/folders/1bSOH-2nB3feFRyDEmiX81CEiWkghss3i
    and place it in AOT-GAN-for-Inpainting/experiments/

    - Install the other image inpainting model:
    git clone https://github.com/hyunobae/AOT-GAN-for-Inpainting.git

8. **test commands (In order)**
    sample is a sample directory
    ### 1. Crop (crop.py)
    ```bash
    python crop.py sample sample_processed --width 640 --height 480
    ```
    *(no "/", sample is your folder containing raw images)

    ### 2. Mask (masking.py)
    ```bash
    python masking.py sample_processed
    ``` 
    *(no "/", sample_processed is your folder containing processed images). saves to /dataset dir

    ### 3. Inpainting (inpaiting.py)
    ```bash
    python inpainting.py dataset/sample_processed --model e2fgvi_hq
    ``` 
    *--mode can be: ('aotgan', 'e2fgvi', 'e2fgvi_hq') saves to result_inpaint dir

    ### 4. Relocating (relocating.py)
    ```bash
    python relocating.py result_inpaint/sample_processed/e2fgvi_hq --mode 0
    ```
    *--mode can be: ('original', 'offset', 'dynamic') saves to result dir

    ### 5. Encoding (encoding.py)
    ```bash
    python encoding.py result/sample_processed/e2fgvi_hq/original
    ```
    *original can be:('original', 'offset', 'dynamic') saves to video dir