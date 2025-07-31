Openrouter models are available at URL=https://openrouter.ai/models

Below are my observations how data elements are displayed

Can you write a python script to parse LLM model information

models are displayed in sections with horizontal line as dividor

item 1 and 2: displayed in one-line
<model name> which is hyper-linked, left aligned, 
<token counts> , right aligned
sicne model name is hyper-linked, please extract its URL

item 2: (optional)
<categories> (with ranking)
because it is optional, some models do not have category info
displayed in one-line

item 3: long text wrapped over 2 lines, even truncated
<model description>

item 4, 5, 6, 7 , 8 delimited by "|"
#4 <by provider>: provider is hyper-linked, please extract its URL
#5 <context window size>, e.g. "200K context"
#6 <pricing for input tokens>, e.g. "$1.25/M input tokens"
#7 <pricing for output tokens>, e.g. "$10/M output tokens"
#8 <pricing for image>, optional, e.g. "$5.16/K input imgs"

