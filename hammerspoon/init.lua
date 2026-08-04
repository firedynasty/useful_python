hs.hotkey.bind({"cmd", "ctrl", "shift"}, "m", function()
    local output = hs.audiodevice.defaultOutputDevice()
    output:setMuted(not output:muted())
end)

-- Dictation: F5 to start/stop recording → transcribe with whisper → AI cleanup → clipboard
local recording = false
local wavFile = "/tmp/mic_dictation_temp.wav"
local textFile = "/tmp/mic_dictation_text.tmp"
local recordJob = nil
local whisperModel = "/opt/homebrew/share/whisper-cpp/ggml-base.bin"

hs.hotkey.bind({}, "F5", function()
  local output = hs.audiodevice.defaultOutputDevice()
  if not recording then
    recording = true
    output:setMuted(true)
    hs.alert.show("🎙 Recording...")
    recordJob = hs.task.new("/opt/homebrew/bin/sox", nil,
      {"-t", "coreaudio", "MacBook Air Microphone", "-r", "16000", "-c", "1", "-b", "16", wavFile})
    recordJob:start()
  else
    recording = false
    output:setMuted(false)
    hs.alert.show("⏳ Transcribing...")
    recordJob:terminate()

    hs.timer.doAfter(1.5, function()
      -- Step 1: Whisper transcription (F5 flow)
      hs.task.new("/bin/sh", function(code, stdout, stderr)
        local text = (stdout or ""):match("^%s*(.-)%s*$")
        if text and #text > 0 then
          -- Write text to temp file so Python can read it safely (avoids shell escaping issues)
          local f = io.open(textFile, "w")
          f:write(text)
          f:close()

          -- Step 2: AI cleanup via Groq llama-3.3-70b-versatile
          local pyScript = [[
import json, urllib.request, os, sys

text = open(']] .. textFile .. [[').read().strip()
data = json.dumps({
  'model': 'llama-3.3-70b-versatile',
  'messages': [
    {'role': 'system', 'content': 'You are a transcription corrector. Fix only obvious speech-to-text errors such as wrong words that sound similar (e.g. "tick" instead of "take"). Do not rephrase or add anything. Return only the corrected text.'},
    {'role': 'user', 'content': text}
  ]
}).encode()

req = urllib.request.Request(
  'https://api.groq.com/openai/v1/chat/completions',
  data=data,
  headers={
    'Authorization': 'Bearer ' + os.environ['GROQ_API_KEY'],
    'Content-Type': 'application/json'
  }
)
resp = json.loads(urllib.request.urlopen(req).read())
print(resp['choices'][0]['message']['content'], end='')
]]

          hs.task.new("/bin/sh", function(code2, stdout2, stderr2)
            local cleaned = (stdout2 or ""):match("^%s*(.-)%s*$")
            if cleaned and #cleaned > 0 and cleaned ~= "null" then
              hs.pasteboard.setContents(cleaned)
            else
              hs.pasteboard.setContents(text)  -- fallback to original whisper text
            end
            hs.eventtap.keyStroke({"cmd"}, "v")
            os.remove(wavFile)
            os.remove(textFile)
          end, {"-c", "source ~/.zshrc && python3 -c '" .. pyScript:gsub("'", "'\\''") .. "'"}):start()

        else
          hs.alert.show("❌ No transcription")
          os.remove(wavFile)
        end
      end, {"-c", "/opt/homebrew/bin/whisper-cli -m '" .. whisperModel .. "' -f '" .. wavFile .. "' --no-timestamps -l auto 2>/dev/null"}):start()
    end)
  end
end)

-- Dictation to TextEdit: ctrl+option+2 to start/stop → append to front TextEdit doc
local recordingTE = false
local wavFileTE = "/tmp/mic_dictation_textedit.wav"
local textFileTE = "/tmp/mic_dictation_textedit.tmp"
local recordJobTE = nil

hs.hotkey.bind({"ctrl", "alt"}, "2", function()
  local output = hs.audiodevice.defaultOutputDevice()
  if not recordingTE then
    recordingTE = true
    output:setMuted(true)
    hs.alert.show("🎙 Recording to TextEdit...")
    recordJobTE = hs.task.new("/opt/homebrew/bin/sox", nil,
      {"-t", "coreaudio", "MacBook Air Microphone", "-r", "16000", "-c", "1", "-b", "16", wavFileTE})
    recordJobTE:start()
  else
    recordingTE = false
    output:setMuted(false)
    hs.alert.show("⏳ Transcribing...")
    recordJobTE:terminate()

    hs.timer.doAfter(1.5, function()
      hs.task.new("/bin/sh", function(code, stdout, stderr)
        local text = (stdout or ""):match("^%s*(.-)%s*$")
        if text and #text > 0 then
          local f = io.open(textFileTE, "w")
          f:write(text)
          f:close()

          local pyScript = [[
import json, urllib.request, os

text = open(']] .. textFileTE .. [[').read().strip()
data = json.dumps({
  'model': 'llama-3.3-70b-versatile',
  'messages': [
    {'role': 'system', 'content': 'You are a transcription corrector. Fix only obvious speech-to-text errors such as wrong words that sound similar. Do not rephrase or add anything. Return only the corrected text.'},
    {'role': 'user', 'content': text}
  ]
}).encode()

req = urllib.request.Request(
  'https://api.groq.com/openai/v1/chat/completions',
  data=data,
  headers={
    'Authorization': 'Bearer ' + os.environ['GROQ_API_KEY'],
    'Content-Type': 'application/json'
  }
)
resp = json.loads(urllib.request.urlopen(req).read())
print(resp['choices'][0]['message']['content'], end='')
]]

          hs.task.new("/bin/sh", function(code2, stdout2, stderr2)
            local cleaned = (stdout2 or ""):match("^%s*(.-)%s*$")
            local final = (cleaned and #cleaned > 0 and cleaned ~= "null") and cleaned or text
            os.remove(wavFileTE)
            os.remove(textFileTE)

            -- Append to front TextEdit document via AppleScript
            -- Put text in clipboard first to avoid any string escaping issues
            hs.pasteboard.setContents(final)
            hs.osascript.applescript([[
              tell application "TextEdit"
                if (count of documents) > 0 then
                  set text of document 1 to (text of document 1) & " " & (the clipboard)
                else
                  make new document
                  set text of document 1 to (the clipboard)
                end if
              end tell
            ]])
            hs.alert.show("✅ Added to TextEdit")
          end, {"-c", "source ~/.zshrc && python3 -c '" .. pyScript:gsub("'", "'\\''") .. "'"}):start()

        else
          hs.alert.show("❌ No transcription")
          os.remove(wavFileTE)
        end
      end, {"-c", "/opt/homebrew/bin/whisper-cli -m '" .. whisperModel .. "' -f '" .. wavFileTE .. "' --no-timestamps -l auto 2>/dev/null"}):start()
    end)
  end
end)

-- Type-to-TextEdit: ctrl+option+` → prompt → append to front TextEdit doc
hs.hotkey.bind({"ctrl", "alt"}, "`", function()
  local ok, result = hs.osascript.applescript([[
    set dialogResult to display dialog "Append to TextEdit:" default answer "" buttons {"Cancel", "Append"} default button "Append" with title "TextEdit Input"
    return text returned of dialogResult
  ]])
  if ok and result and #result > 0 then
    hs.pasteboard.setContents(result)
    hs.osascript.applescript([[
      tell application "TextEdit"
        if (count of documents) > 0 then
          set text of document 1 to (text of document 1) & " " & (the clipboard)
        else
          make new document
          set text of document 1 to (the clipboard)
        end if
      end tell
    ]])
    hs.alert.show("✅ Added to TextEdit")
  end
end)
