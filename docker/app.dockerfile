FROM ubuntu:latest

ARG APP_USER=zerod
ARG PYTHONUNBUFFERED=1
ARG PYTHONDONTWRITEBYTECODE=1
ARG PY_VERSION=3.12.8
ENV HOME=/home/${APP_USER}
# Set environment variables
ENV PYENV_ROOT="/home/${APP_USER}/.pyenv" \
  PATH="/home/${APP_USER}/.pyenv/bin:/home/${APP_USER}/.pyenv/shims:/home/${APP_USER}/.pyenv/versions/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  curl \
  git \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  libffi-dev \
  liblzma-dev \
  supervisor \
  ca-certificates \
  sudo \
  vim \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -ms /bin/bash ${APP_USER} && \
  echo "${APP_USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to non-root user
USER ${APP_USER}
WORKDIR /home/${APP_USER}/app

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT && \
  git clone https://github.com/pyenv/pyenv-virtualenv.git $PYENV_ROOT/plugins/pyenv-virtualenv && \
  echo 'eval "$(pyenv init --path)"' >> ~/.bashrc && \
  echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
  echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Reload shell to use pyenv (Dockerfile RUN commands need manual loading)
SHELL ["/bin/bash", "-c"]

# Install Python version and create virtual environment
ARG PYTHON_VERSION=3.12.8
RUN pyenv install $PY_VERSION
# pyenv virtualenv $PYTHON_VERSION myenv && \
# echo 'pyenv activate myenv' >> ~/.bashrc && \
# pyenv activate myenv
# Create a virtual environment using the specific Python version
RUN $PYENV_ROOT/versions/$PY_VERSION/bin/python -m venv .venv

# Update PATH to use the virtual environment directly
ENV PATH="/home/${APP_USER}/app/.venv/bin:$PATH"


# Install pip packages in the virtual environment

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY streamlit_app.py main.py ./

# Install and configure Supervisor
USER root
COPY supervisor-file/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ENV PATH="/home/${APP_USER}/app/.venv/bin:$PATH"

# Expose necessary ports
EXPOSE 8000

# Start Supervisor
CMD ["/usr/bin/supervisord"]

