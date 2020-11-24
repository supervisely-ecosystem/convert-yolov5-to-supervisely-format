# run from repo root with commands:
# docker login (one time step)
# sudo chmod +x ./docker/prepare_dockerimage.sh
# ./docker/prepare_dockerimage.sh

VERSION='1.0.0'

BASE_DOCKER_IMAGE='supervisely/base-py-sdk:6'

DOCKER_IMAGE='supervisely/convert-yolov5-to-supervisely'
DOCKER_IMAGE_LATEST=$DOCKER_IMAGE':latest'
DOCKER_IMAGE_VERSION=$DOCKER_IMAGE':'$VERSION

docker pull $BASE_DOCKER_IMAGE && \
docker build --build-arg BASE_IMAGE=$BASE_DOCKER_IMAGE -t $DOCKER_IMAGE_LATEST -f docker/Dockerfile . && \
docker build --build-arg BASE_IMAGE=$BASE_DOCKER_IMAGE -t $DOCKER_IMAGE_VERSION -f docker/Dockerfile . && \

#uncomment manually + be sure that you will not rewrite existing version(tag) in registry
docker push $DOCKER_IMAGE_LATEST
docker push $DOCKER_IMAGE_VERSION

echo 'Pushed images:'
echo $DOCKER_IMAGE_LATEST
echo $DOCKER_IMAGE_VERSION
