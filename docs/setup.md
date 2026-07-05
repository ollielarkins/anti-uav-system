# Development Environment Setup

WSL2 (Ubuntu 22.04) + ROS2 Humble + Gazebo Classic 11 + ArduPilot SITL.
The HUD (React/Electron) runs natively on Windows and connects to ROS over WebSocket.

**Time to complete: ~45–60 minutes** (most of it is download/install waiting)

---

## Prerequisites

- Windows 11 (Build 22000+)
- NVIDIA GPU recommended for YOLOv8 inference (CPU fallback works at ~15fps)
- 20GB free disk space

---

## Step 1 — Enable WSL2

Open PowerShell as Administrator:

```powershell
wsl --install
wsl --set-default-version 2
```

Reboot when prompted.

Then install Ubuntu 22.04:

```powershell
wsl --install -d Ubuntu-22.04
```

Launch it from Start → "Ubuntu 22.04". Create a username + password when prompted.

---

## Step 2 — Ubuntu Base Setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git wget build-essential python3-pip python3-venv
```

---

## Step 3 — ROS2 Humble

```bash
# Locale
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ROS2 apt repo
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install
sudo apt update
sudo apt install -y ros-humble-desktop python3-colcon-common-extensions python3-rosdep

# Init rosdep
sudo rosdep init
rosdep update

# Auto-source in every shell
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Verify:
```bash
ros2 --version
# ros2cli 0.18.x
```

---

## Step 4 — Gazebo Classic 11

Gazebo Classic (not Gazebo Garden) — better ArduPilot SITL support.

```bash
sudo apt install -y gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-plugins

# Verify
gazebo --version
# Gazebo multi-robot simulator, version 11.x
```

---

## Step 5 — ArduPilot SITL

```bash
cd ~
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot

# Install deps
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile

# Build ArduCopter SITL
./waf configure --board sitl
./waf copter

# Verify (should print SITL params and exit)
./Tools/autotest/sim_vehicle.py -v ArduCopter --no-rebuild -w --help
```

ArduPilot Gazebo plugin (bridges SITL ↔ Gazebo):

```bash
cd ~
git clone https://github.com/khancyr/ardupilot_gazebo.git
cd ardupilot_gazebo
mkdir build && cd build
cmake ..
make -j4
sudo make install

echo "source /usr/share/gazebo/setup.sh" >> ~/.bashrc
echo "export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$HOME/ardupilot_gazebo/models" >> ~/.bashrc
echo "export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$HOME/ardupilot_gazebo/build" >> ~/.bashrc
source ~/.bashrc
```

---

## Step 6 — Python Dependencies

```bash
pip3 install numpy scipy ultralytics opencv-python-headless

# Verify YOLOv8
python3 -c "from ultralytics import YOLO; print('YOLOv8 OK')"
```

---

## Step 7 — ROS Bridge + Video Server

```bash
sudo apt install -y \
  ros-humble-rosbridge-server \
  ros-humble-web-video-server \
  ros-humble-cv-bridge \
  ros-humble-vision-msgs

# Verify
ros2 pkg list | grep rosbridge
# rosbridge_server
```

---

## Step 8 — Build the ROS2 Package

Mount the Windows repo inside WSL2 (it's auto-mounted at `/mnt/c/`):

```bash
# Create a symlink so ROS finds the package
ln -s /mnt/c/Users/ozzal/anti-uav-system ~/anti-uav-system
cd ~/anti-uav-system

# Build
colcon build --symlink-install
source install/setup.bash
echo "source ~/anti-uav-system/install/setup.bash" >> ~/.bashrc
```

Verify:
```bash
ros2 pkg list | grep anti_uav
# anti_uav_system
```

---

## Step 9 — GPU Setup (NVIDIA, optional but recommended)

Required for YOLOv8 to run at 30fps. Skip this if CPU-only is acceptable.

On **Windows** (not WSL), install the [NVIDIA CUDA WSL2 driver](https://developer.nvidia.com/cuda/wsl).
Do **not** install CUDA inside WSL — the Windows driver exposes CUDA automatically.

Inside WSL2:
```bash
# Check GPU is visible
nvidia-smi
# Should show your GPU

# Install PyTorch with CUDA
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Verify
python3 -c "import torch; print(torch.cuda.is_available())"
# True
```

---

## Step 10 — VS Code (Windows)

Install the **WSL** extension in VS Code. Then from WSL terminal:

```bash
code ~/anti-uav-system
```

VS Code opens on Windows but executes inside WSL2 — full IntelliSense, terminal, git.

---

## Step 11 — Node.js for HUD (Windows)

The HUD runs natively on Windows (no WSL needed):

Download and install [Node.js LTS](https://nodejs.org) on Windows.

```powershell
# In Windows PowerShell, from the repo root
cd hud
npm install
npm start
```

The HUD connects to rosbridge at `ws://localhost:9090`. ROS runs in WSL2, which exposes ports to Windows automatically — no port forwarding needed.

---

## Verify Full Stack

```bash
# Terminal 1 — ROS2 core + bridge
source ~/anti-uav-system/install/setup.bash
ros2 launch anti_uav_system main.launch.py

# Terminal 2 — check topics are live
ros2 topic list
# /camera/image_raw
# /detections
# /tracks
# /ballistics
```

---

## Quick Reference

| What | Where | Command |
|------|-------|---------|
| ROS2 workspace | `~/anti-uav-system` (symlink) | `source install/setup.bash` |
| Solver tests | Windows or WSL | `python -m solver.ballistics` |
| Full launch | WSL | `ros2 launch anti_uav_system main.launch.py` |
| HUD | Windows | `cd hud && npm start` |
| Gazebo GUI | WSL (X11 via WSLg) | auto-launched by launch file |

WSLg (included in Windows 11) handles the Gazebo GUI window — no separate X server needed.
