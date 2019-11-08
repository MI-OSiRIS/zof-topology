FROM ubuntu:16.04

MAINTAINER OpenLab <gskipper@indiana.edu>

RUN apt-get update
RUN apt-get -y install vim sudo software-properties-common


RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN set -ex \
    && buildDeps=' \
        git \
    ' \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys FFBE06FBB4EDC679174DD2CCD5AA2ED445128570 \
    && echo "deb http://ppa.launchpad.net/byllyfish/oftr/ubuntu xenial main" >> /etc/apt/sources.list \
    && apt-get update && apt-get install -y --no-install-recommends \
        $buildDeps \
        oftr \
        python3.6 \
        python3-pip \
        python3-setuptools \
    && pip3 install git+https://github.com/byllyfish/zof.git \ 
    && rm -rf /var/lib/apt/lists/*


RUN mkdir /home/zof
ENV HOME /home/zof
WORKDIR $HOME
RUN cd $HOME

RUN git config --global user.email "zof@zof"
RUN git config --global user.name "ZOF"

RUN git clone https://github.com/MI-OSiRIS/zof-topology.git
RUN git clone -b develop https://github.com/periscope-ps/unisrt
RUN git clone -b master https://github.com/periscope-ps/lace

COPY example_config.ini $HOME/zof/

ADD build.sh .
RUN bash ./build.sh

ADD run.sh .
CMD bash ./run.sh
