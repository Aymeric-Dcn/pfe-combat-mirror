# Adds our RT-COSMIK setup on top of the image from MaximeSabbah/cosmik-dev-container.
#
#   git clone https://github.com/MaximeSabbah/cosmik-dev-container.git
#   cd cosmik-dev-container/.devcontainer && docker build -t mmpose_image .
#   cd /path/to/pfe-combat-mirror && docker build -f docker/Dockerfile -t pfe_cosmik .
#
# Models are fetched at first start: the TensorRT engine has to be built on the GPU.
FROM mmpose_image

COPY . /root/pfe-combat-mirror
RUN bash /root/pfe-combat-mirror/scripts/tools/setup_rtcosmik_main.sh --no-models

WORKDIR /root/workspace/ros_ws/RT-COSMIK-main
CMD ["bash"]
