## [Version 1.1.0] -2025-01-26
**Relocating modes for 16:9 to 9:16 (wide to narrow, short to high)**
*pending changes to be made to fic 7.2

TODO: 
- allow mode to have more numbers for MODE and its derivatives in the script: 0-4 for bulk and master
- relocating.py relocator new mode 
- prepforharmonizer.py and encoding.py allow more modes
##### w2p:
```bash
./scripts/bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\src\DAVIS-test\JPEGImages\480p e2fgvi_hq 3 --inpaint-only --crop_to_width 854 --crop_to_height 480 --target_width 480 --target_height 854
./scripts/bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\src\DAVIS-test\JPEGImages\480p e2fgvi_hq 3 --relocating-only --crop_to_width 854 --crop_to_height 480 --target_width 480 --target_height 854
./scripts/add_harmonization.sh --width 480 --height 854 --mode 3
```
##### p2w:
```bash
./scripts/bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\src\DAVIS-test\JPEGImages\480p e2fgvi_hq 4 --inpaint-only --crop_to_width 480 --crop_to_height 854 --target_width 854 --target_height 480
./scripts/bulk.sh C:\Users\User\Desktop\FYP\Fix-ORPVR\src\DAVIS-test\JPEGImages\480p e2fgvi_hq 4 --inpaint-only --crop_to_width 480 --crop_to_height 854 --target_width 854 --target_height 480
./scripts/add_harmonization.sh --width 854 --height 480 --mode 4
```


## [Version 1.0.0] - 2025-01-17
### Added
- SAM2 + Hamonizer to ORPVR

### Changed
- Added a movetosam2-override folder so that any changes can be copied over to sam2 folder for user since sam2 can only be executed from the sam2 folder

### Fixed
- SAM2 unable to be executed in another directory