FROM ubuntu:latest
# add the aws config to the root directory
ADD .aws /root/.aws
# Add crontab file in the cron directory
ADD crontab /etc/cron.d/hello-cron

# Set the timezone to IST
ENV TZ=Asia/Kolkata
# Give execution rights on the cron job and add timezone
RUN chmod 0644 /etc/cron.d/hello-cron && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# copy the requirements file into the image
COPY . /app

# switch working directory
WORKDIR /app

# Install additional requirements and do some configurations
RUN apt-get update && apt-get install -y build-essential awscli cron libmysqlclient-dev python3-pip python3-tk -y && \
     pip3 install -r requirements.txt && \
     touch /root/error.log && \
     chmod +x dumpLogToS3.sh

# Start Cron at container startup
CMD cron && python3 manage.py