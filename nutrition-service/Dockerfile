FROM python:3.7.5

# Set the working directory to /nutrition-service
WORKDIR /nutrition-service

# Install any needed packages specified in requirements.txt
ADD requirements.txt /nutrition-service
RUN pip install -r requirements.txt

RUN mkdir -p /nutrition/uploads

# Copy the current dir contents into container at /nutrition-service
ADD . /nutrition-service

# Make port 1337 available outside this container
EXPOSE 1337

CMD ["python", "nutrition_service.py"]
