stages:
  - package

.package-base:
  image: $CI_SERVER_HOST:5050/libretro-infrastructure/libretro-build-amd64-ubuntu:latest
  stage: package
  variables:
    MEDIA_PATH: .media
  script:
    - make INSTALLDIR=${MEDIA_PATH}/${CI_PROJECT_NAME} install
  artifacts:
    paths:
    - ${MEDIA_PATH}
    expire_in: 1 day

libretro-package-any:
  extends: .package-base
