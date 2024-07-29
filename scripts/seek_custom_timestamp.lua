-- Lua script for MPV to seek to a custom timestamp

local options = require 'mp.options'

-- Define the options with default values
local o = {
    minutes = 0,
    seconds = 5,
    Customkey1 = "/",   -- Default key binding is /
    Customkey2 = "?"   -- Default key binding is ?
}

-- Read the options from the seek_custom_timestamp.conf file
options.read_options(o, "seek_custom_timestamp")

-- Function to convert minutes and seconds to seconds
function convert_to_seconds(minutes, seconds)
    return (minutes * 60) + seconds
end

-- Function to seek to the specified timestamp from options
function seek_to_custom_timestamp()
    local timestamp = convert_to_seconds(o.minutes, o.seconds)
    mp.commandv("seek", timestamp, "absolute")
    mp.osd_message(string.format("Seeking to %d:%02d", o.minutes, o.seconds), 2)
end

-- Function to seek to the hardcoded 90 seconds
function seek_to_90_seconds()
    local timestamp = convert_to_seconds(1, 30) -- 1 minute and 30 seconds
    mp.commandv("seek", timestamp, "absolute")
    mp.osd_message("Seeking to 1:30", 2)
end

-- Register the key binding for seeking to 90 seconds
mp.add_key_binding(o.Customkey2, "seek_to_90_seconds", seek_to_90_seconds)

-- Register/Set the key binding from the configuration file
mp.add_key_binding(o.Customkey1, "seek_to_custom_timestamp", seek_to_custom_timestamp)