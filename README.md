# LLM Finder

Explore LLM models available at OpenRouter

## Streamlit App

![welcome](https://github.com/digital-duck/llm_finder/blob/main/docs/img/0-LLM-Model-Finder.png?raw=true)

![1-AI Chat](https://github.com/digital-duck/llm_finder/blob/main/docs/img/1-Chat.png?raw=true)

![2-Browse Model](https://github.com/digital-duck/llm_finder/blob/main/docs/img/2-Browse.png?raw=true)

![3-overview](https://github.com/digital-duck/llm_finder/blob/main/docs/img/3-overview.png?raw=true)

![4-Analytics](https://github.com/digital-duck/llm_finder/blob/main/docs/img/4-Analytics.png?raw=true)

![5-Recommend](https://github.com/digital-duck/llm_finder/blob/main/docs/img/5-Recommend.png?raw=true)

![6-Load-Model](https://github.com/digital-duck/llm_finder/blob/main/docs/img/6-Load-Model.png?raw=true)



## Setup
```bash
# create virtual env
conda create -n openrouter python=3.11
conda activate openrouter

# clone repo
git clone https://github.com/digital-duck/llm_finder.git
cd llm_finder

# install dependency
pip install -r requirements.txt

# obtain API Key from https://openrouter.ai/
# required for loading new model info 
# otherwise use a local .csv file
export OPENROUTER_API_KEY=<your-own-API-KEY>

cd src

# launch app
streamlit run LLM_Model_Finder.py

```

