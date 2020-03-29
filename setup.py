import setuptools

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name="mijiahygrothermolib",
    version="0.0.1",
    author="Aral Can Kaymaz",
    author_email="aralcan@hotmail.com",
    description="A package to discover and read values from a Xiaomi Mijia BLE Sensor",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/heironeous/mijiahygrothermolib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
