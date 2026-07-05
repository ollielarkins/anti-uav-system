#!/bin/bash
# Run this inside WSL2 (Ubuntu 22.04) after the reboot.
# Command: bash /mnt/c/Users/ozzal/anti-uav-system/scripts/2_wsl_setup.sh
#
# Installs: ROS2 Humble, Gazebo Classic 11, ArduPilot SITL,
#           Python deps, ROCm 6.1 (AMD RX 6600), PyTorch ROCm,
#           rosbridge, web_video_server. Then builds the ROS2 package.

set -e  # exit on any error

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
step()  { echo -e "\n${CYAN}[$(date +%H:%M:%S)] $1${NC}"; }
ok()    { echo -e "${GREEN}✓ $1${NC}"; }
warn()  { echo -e "${YELLOW}⚠ $1${NC}"; }

REPO=/mnt/c/Users/ozzal/anti-uav-system

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       Anti-UAV System — WSL2 Environment Setup      ║"
echo "║       Ubuntu 22.04 · ROS2 Humble · Gazebo · ROCm    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Base packages ──────────────────────────────────────────────────────────
step "1/9 — Base packages"
sudo apt-get update -q
sudo apt-get install -y -q \
    curl wget git build-essential python3-pip python3-venv \
    locales software-properties-common lsb-release gnupg
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
ok "Base packages installed"

# ── 2. ROS2 Humble ────────────────────────────────────────────────────────────
step "2/9 — ROS2 Humble"
if ros2 --version &>/dev/null; then
    warn "ROS2 already installed, skipping"
else
    sudo add-apt-repository universe -y
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
        -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
        http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
        | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt-get update -q
    sudo apt-get install -y -q ros-humble-desktop python3-colcon-common-extensions python3-rosdep
    sudo rosdep init 2>/dev/null || true
    rosdep update
    grep -qxF 'source /opt/ros/humble/setup.bash' ~/.bashrc \
        || echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
    source /opt/ros/humble/setup.bash
    ok "ROS2 Humble installed"
fi

# ── 3. Gazebo Classic 11 ──────────────────────────────────────────────────────
step "3/9 — Gazebo Classic 11 + ROS2 integration"
if gazebo --version &>/dev/null; then
    warn "Gazebo already installed, skipping"
else
    sudo apt-get install -y -q \
        gazebo ros-humble-gazebo-ros-pkgs ros-humble-gazebo-plugins
    ok "Gazebo installed"
fi

# ── 4. ROS2 comms packages ────────────────────────────────────────────────────
step "4/9 — rosbridge + video server + cv_bridge"
sudo apt-get install -y -q \
    ros-humble-rosbridge-server \
    ros-humble-web-video-server \
    ros-humble-cv-bridge \
    ros-humble-vision-msgs
ok "ROS2 comms packages installed"

# ── 5. ArduPilot SITL ────────────────────────────────────────────────────────
step "5/9 — ArduPilot SITL"
if [ -d "$HOME/ardupilot" ]; then
    warn "ArduPilot already cloned, skipping clone"
else
    git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git "$HOME/ardupilot"
fi
cd "$HOME/ardupilot"
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
if [ ! -f "build/sitl/bin/arducopter" ]; then
    ./waf configure --board sitl
    ./waf copter
    ok "ArduPilot SITL built"
else
    warn "ArduPilot already built, skipping"
fi

# ── 6. ArduPilot Gazebo plugin ───────────────────────────────────────────────
step "5b/9 — ArduPilot Gazebo plugin"
if [ -d "$HOME/ardupilot_gazebo" ]; then
    warn "ardupilot_gazebo already cloned, skipping"
else
    git clone https://github.com/khancyr/ardupilot_gazebo.git "$HOME/ardupilot_gazebo"
    cd "$HOME/ardupilot_gazebo"
    mkdir -p build && cd build
    cmake .. && make -j"$(nproc)"
    sudo make install
    ok "ArduPilot Gazebo plugin built"
fi

grep -qxF 'source /usr/share/gazebo/setup.sh' ~/.bashrc \
    || echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
grep -q 'ardupilot_gazebo/models' ~/.bashrc \
    || echo 'export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$HOME/ardupilot_gazebo/models' >> ~/.bashrc
grep -q 'ardupilot_gazebo/build' ~/.bashrc \
    || echo 'export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$HOME/ardupilot_gazebo/build' >> ~/.bashrc

# ── 7. Python deps ───────────────────────────────────────────────────────────
step "6/9 — Python dependencies (numpy, scipy, ultralytics, opencv)"
pip3 install --quiet numpy scipy ultralytics opencv-python-headless
ok "Python deps installed"

# ── 8. AMD ROCm 6.1 ──────────────────────────────────────────────────────────
step "7/9 — AMD ROCm 6.1 (RX 6600 / gfx1032)"
if rocm-smi &>/dev/null; then
    warn "ROCm already installed, skipping"
else
    cd /tmp
    wget -q https://repo.radeon.com/amdgpu-install/6.1.1/ubuntu/jammy/amdgpu-install_6.1.60101-1_all.deb
    sudo apt-get install -y -q ./amdgpu-install_6.1.60101-1_all.deb
    sudo amdgpu-install -y --usecase=rocm --no-dkms
    sudo usermod -aG render,video "$USER"
    ok "ROCm installed — you'll need to log out/in once for group changes to take effect"
fi

# gfx1032 override — prevents ROCm misidentifying Navi 23 in WSL2
grep -qxF 'export HSA_OVERRIDE_GFX_VERSION=10.3.0' ~/.bashrc \
    || echo 'export HSA_OVERRIDE_GFX_VERSION=10.3.0' >> ~/.bashrc
export HSA_OVERRIDE_GFX_VERSION=10.3.0

# ── 9. PyTorch ROCm ──────────────────────────────────────────────────────────
step "8/9 — PyTorch with ROCm 6.1"
if python3 -c "import torch; assert torch.cuda.is_available()" &>/dev/null; then
    warn "PyTorch ROCm already installed and GPU visible, skipping"
else
    pip3 install --quiet torch torchvision \
        --index-url https://download.pytorch.org/whl/rocm6.1
    ok "PyTorch ROCm installed"
fi

# ── 10. Build ROS2 package ────────────────────────────────────────────────────
step "9/9 — Build anti_uav_system ROS2 package"
source /opt/ros/humble/setup.bash

# Symlink repo into home if not already done
if [ ! -L "$HOME/anti-uav-system" ]; then
    ln -s "$REPO" "$HOME/anti-uav-system"
fi

cd "$HOME/anti-uav-system"
colcon build --symlink-install --event-handlers console_cohesion+

grep -qxF "source $HOME/anti-uav-system/install/setup.bash" ~/.bashrc \
    || echo "source $HOME/anti-uav-system/install/setup.bash" >> ~/.bashrc
source install/setup.bash
ok "ROS2 package built"

# ── Done ─────────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "Verifying installs..."
ros2 --version && ok "ROS2 OK"
gazebo --version 2>&1 | head -1 && ok "Gazebo OK"
python3 -c "from ultralytics import YOLO; print('YOLOv8 OK')" && ok "YOLOv8 OK"
python3 -c "import torch; print(f'PyTorch {torch.__version__}, GPU: {torch.cuda.is_available()}')"

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Close and reopen WSL2 (applies ROCm group + bashrc changes)"
echo "  2. Verify GPU: rocm-smi"
echo "  3. Launch system: ros2 launch anti_uav_system main.launch.py"
echo "  4. On Windows: cd hud && npm install && npm start"
