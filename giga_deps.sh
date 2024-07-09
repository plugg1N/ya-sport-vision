pip install wget
apt-get install sox libsndfile1 ffmpeg
pip install matplotlib

python -m pip install git+https://github.com/NVIDIA/NeMo.git@1fa961ba03ab5f8c91b278640e29807079373372#egg=nemo_toolkit[all]
python -m pip install pyannote.audio==3.2.0

cd CTC-config
wget https://n-ws-q0bez.s3pd12.sbercloud.ru/b-ws-q0bez-jpv/GigaAM/ctc_model_weights.ckpt
wget https://n-ws-q0bez.s3pd12.sbercloud.ru/b-ws-q0bez-jpv/GigaAM/ctc_model_config.yaml

cd ..