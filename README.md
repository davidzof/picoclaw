# Picoclaw Configuration and Skills

You have probably heard a lot about OpenClaw recently and the derivatives like nanoclaw and picoclaw and wondered what all the hype is about.

I want to explain what PicoClaw is and how PicoClaw compares to OpenClaw. We’ll then look at creating a single skill with no coding then something more advanced.

<div style="display: inline-flex; align-items: center;">
  <!-- Video Thumbnail -->
  <a href="[https://www.youtube.com/watch?v=5yLzZikS15k](https://www.youtube.com/embed/0J8p2Vyfu-M?si=Yla8myGXzdYMMgXc)" target="_blank" style="display: inline-block;">
    <img width="1536" height="1024" alt="pico-vs-open" src="https://github.com/user-attachments/assets/46467d60-dd28-4cbe-b767-decb210872e9" />
  </a>

  <!-- Play Button -->
  <a href="https://www.youtube.com/watch?v=5yLzZikS15k" target="_blank" style="display: inline-block;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_play_button_icon_%282013%E2%80%932017%29.svg" 
         style="width: 50px; height: auto; margin-left: 5px;">
  </a>
</div>

PicoClaw is an open-source AI agent project written in Go, designed to be very lightweight and portable. The project describes itself as an ultra-lightweight personal AI assistant that can run on very modest hardware, and it emphasizes low memory use, fast startup, and a single-binary deployment model. PicoClaw is neither an AI itself nor a chatbot, at its core is an Agent Loop. That means it can receive a request, decide to use local tools, run those tools, inspect the results, and continue until it has an answer. It is often referred to an AI orchestrator. Rather than the end user interacting with an LLM like OpenAI or Gemini PicoClaw does this using their APIs. Requests are sent in JSON format, the LLM responds and the agent decides whether or not the request is satisfied. This means that context is retained during the loop and the agent can even retain information (context) in its memory and session stores for use in later requests.

Instead of only generating text, PicoClaW can also interact with files, shell commands, web tools, and other capabilities exposed to it by the runtime. Of course this means it has access to the underlying computer so you have to be careful where and how you run it and what access you give it to resources.

<img width="1536" height="1024" alt="agent-loop" src="https://github.com/user-attachments/assets/66c74d39-c9a4-4b10-bf41-137789eb1165" />

## PicoClaw vs OpenClaw

OpenClaw was one of the original AI orchestrators and has gained considerable momentum. PicoClaw is not a fork of OpenClaw; the PicoClaw project says it was built from scratch in Go. But the two projects are close and PicoClaw even added a migration command for OpenClaw workspaces because the workspace structures are very similar.

The big difference is the design philosophy.

OpenClaw is generally the heavier, more full-featured ecosystem. PicoClaw is stripped-down and lightweight aimed at low-resource environments. It can even run on a $10 microcontroller. It claims much lower memory usage and much faster startup than OpenClaw.

## PicoClaw Config

This repo contains the config I use (OpenRouter for the LLM)

## Extending Open/PicoClaw with Skills

If you’ve seen a Open/PicoClaw skill before, it can look surprisingly simple, sometimes it’s just a SKILL.md file with instructions in it. That can make the whole system feel a bit mysterious at first, because you naturally ask: if it’s just Markdown, what is actually doing the work?

## Skills in this Repo

  * simple skill to give the user's IP address and location
  * Brief - Download and analyze stock information based on their tickers
  * Market Watch - Extract news headlines related to the stock tickers 
  * Analysis - Combine the Brief and Market Watch output to analyze current share prices

### Lets break it down using a simple IP skill example

We're going to use PicoClaw for these examples but they could also run on OpenClaw. In the ip directory there is a [SKILL.md](ip/SKILL.md) file. Inside that file, we describe something like this:

_“To get the public IP address, run curl -s "https://ipapi.co/json/" and use the returned JSON to answer the user.”_

What is interesting here is that PicoClaw does not treat that skill as a compiled plugin. Instead, it exposes a set of core tools from the platform it runs on, things like reading files and executing shell commands, the model uses those tools to interpret the skill and carry it out. If you turn on debug is shows core tools such as read_file, write_file, list_dir, and exec being registered.

### What is happening step by step

When the user types:

“/use ip what is my public ip?”

here is the rough sequence.
1. PicoClaw sends the model a structured request containing system instructions, the conversation history, and the available tools.
2. . The model decides it needs to inspect the IP skill, so it asks PicoClaw to read skills/ip/SKILL.md.
3. After reading the skill, the model decides which real tool to use. In this case, it typically chooses the exec tool and constructs a command like:
    curl -s "https://ipapi.co/json/"
4. PicoClaw executes that command locally and captures the output.
5. PicoClaw sends the command output back to the model.
6. Finally, the model turns the raw JSON into a user-friendly response, such as:
    “Your public IP address is this, and it appears to be located in Lyon, France.”

That is the key architecture: the model decides what to do, and PicoClaw executes it safely through its registered tools.

### This can seem strange

Claw skills can feel both powerful and a bit strange. The normal plugin system is usually rigid:

1. you define a function,
2. the framework calls the function,and the result comes back.
   
PicoClaw skills are more like instructions for the model. So the system is split in two:
1. PicoClaw provides the tools and the execution environment.
2. The LLM reads the skill and decides how to use those tools.

That is also why skills can sometimes go wrong if they are vague. If the instructions are unclear, the model can misinterpret them. In testing, that is exactly the kind we saw. The SKILL.md file was being overwritten by PicoClaw because the LLM (Grok) told it to put the result here. We added a line in the SKILL.md file to tell the LLM not to do this. The SKILL.md file also didn't contain the "command" information originally despite referencing this in the description. The LLM spotted this, saw a url in homepage section and surmised that PicoClaw should run _curl_ on this url to get the results. So despite the bug the SKILL still worked correctly. This is very clever but these kind of bugs should always be fixed as they are inefficient and consume both requests and tokens (words) on the LLM which can be costly. You can check how your skill is executed by running PicoClaw in debug mode (see video above).

### Are Skills efficient?
And this raises an important question: Wouldn’t plain coding often be simpler and more efficient?

In many cases, yes.

If all you want is the public IP address, a small Python script or a single curl command is clearly faster, cheaper, and more deterministic than involving an LLM in the loop. So for fixed, well-defined tasks, traditional coding is usually the better engineering choice.

Where PicoClaw becomes interesting is when the workflow is not fixed:
  * when the agent has to choose between tools,
  * read instructions dynamically,
  * inspect outputs,
  * and retry,
  * or chain multiple steps together.

In other words, PicoClaw shines when you want orchestration and reasoning, not just raw execution.

For simple tasks, write code.
For flexible, multi-step, tool-using workflows, PicoClaw becomes valuable.

### Share Price Skill (Brief)

My actual aim was to use PicoClaw to analyze share prices. To this aim I wrote a [Python script] that uses yahooquery to pull historical price data and calculate:
1. 1-day return
2. 5-day return
3. distance from the 20-day moving average
4. volume vs average

and assigns a simple signal like extended_up

After testing this on the command line I wrote a Skill to wrap this code so PicoClaw can answer the question: _“What are these stocks doing right now?”_



### Market Information Skill (Market Watch)

### Analysis Skill

#### Example of use

$ picoclaw agent

🦞 You: compare AKE.PA and AI.PA

🦞 _Both AKE.PA and AI.PA are currently showing an "extended_up" signal, trading above their 20-day moving averages. AKE.PA emerges as the stronger recent mover with a 3.15% gain over the past five days, while AI.PA has been nearly flat with a -0.02% return. Despite this divergence in short-term performance, both stocks are only moderately extended above their moving averages—5.76% for AKE.PA and 3.63% for AI.PA—and both are trading on extremely light volume, at just 5% of their average 20-day volume. This suggests limited conviction behind the moves.

The broader market context is dominated by oil price volatility driven by US-Iran ceasefire developments. Recent headlines show oil swinging dramatically on ceasefire hopes and concerns, with one report noting a $950 million bet on falling oil prices ahead of the ceasefire announcement, followed by multiple 6-9% price swings as the situation evolved. Energy-sensitive sectors are reacting to these macro developments, with broad sector moves appearing driven by geopolitical events rather than company-specific news.

This macro context directly explains the behavior of both AKE.PA (Aker ASA) and AI.PA (Air Liquide), which are energy-related stocks sensitive to oil prices. The modest gains and notably light volume indicate these moves are primarily macro-driven rather than fueled by individual company catalysts. AKE.PA's slightly stronger five-day performance may reflect greater sensitivity to oil price fluctuations, but both stocks are participating in the same sector-wide trend. The "extended_up" signal fits the pattern: oil price volatility has lifted energy stocks above their moving averages, though the anemic volume suggests traders remain cautious about the sustainability of the ceasefire and its impact on energy markets._

🦞 You: analyse DOW
 
🦞 _DOW (Dow Inc.) is currently displaying an "extended_down" signal, trading 6.74% below its 20-day moving average with an 8.33% decline over the past five trading days, indicating a clear short-term downtrend. However, the stock showed a notable 3.29% bounce in the most recent session, offering some relief from the broader decline. Trading volume on this bounce was slightly below average at 79% of the 20-day average, suggesting moderate conviction behind the recovery attempt. The stock appears to be caught in a corrective phase, with the extended_down signal reflecting the recent weakness.

The broader market context is dominated by geopolitical developments surrounding US-Iran ceasefire negotiations, which have triggered extreme oil price volatility. Recent headlines show oil swinging wildly—rising 6% on ceasefire collapse fears, then falling 9% after Iran declared the Strait of Hormuz open and expectations that talks will proceed. Energy-sensitive sectors are reacting sharply to these macro events, with broad-based moves driven by geopolitical factors rather than company-specific news.

This macro context directly explains DOW's behavior as a chemicals company highly sensitive to oil price fluctuations and economic conditions. The five-day decline aligns with periods of oil price uncertainty and potential supply disruptions that increase feedstock costs and economic uncertainty. The recent bounce coincides with headlines about oil falling on improved ceasefire prospects, which would lower input costs and ease economic pressures. The below-average volume on the bounce indicates traders are cautiously responding to macro-driven price swings rather than fundamental catalysts, making DOW's recent action primarily a reflection of energy market volatility during this geopolitical episode._
