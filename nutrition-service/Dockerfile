FROM python:3.6.2

# Set the working directory to /image-service
WORKDIR /image-service

# Install any needed packages specified in requirements.txt
ADD requirements.txt /image-service
RUN pip install -r requirements.txt

RUN mkdir -p /images/uploads

# Copy the current dir contents into container at /image-service
ADD . /image-service

# Make port 3000 available outside this container
EXPOSE 3000

CMD ["python", "image_service.py"]
