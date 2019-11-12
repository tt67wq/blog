## python 相关
---

#### pyenv
```
git clone --depth=1 https://github.com/yyuu/pyenv.git ~/.pyenv
git clone --depth=1 https://github.com/yyuu/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv

echo 'export PYENVROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENVROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc

pyenv virtualenv 2.7.10 env2710
pyenv activate env2710
```