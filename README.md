Execute these commands prior to doing the lab:

``` bash
git clone https://github.com/Dynatrace-PDP/dtu_sandbox_logs.git
sudo usermod -aG docker dt_training
newgrp docker
cd dtu_sandbox_logs
chmod +x initialize.sh
./initialize.sh
```

You may have to paste in the password for sudo, which is the same password you used to login to the instance.