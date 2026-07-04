--------------------------------------------------
-- collab_notebook_sub.lua
--------------------------------------------------
-- Author:  lilhawkeye2002
-- Contact: lilhawkeye2002@gmail.com
-- Discord: synthscribe
-- Repository:
--     https://github.com/lilhawkeye2002-ux/Whisper_Notebooks
-- Created: 2026-06-05
-- Purpose:
--     This MPV Lua script provides an interactive subtitle
--     styling editor designed to closely mirror the subtitle
--     styling controls available in the Whisper_Notebooks
--     Google Colab notebooks.
--
--     The goal is to allow users to visually preview and
--     fine-tune subtitle appearance directly inside MPV while
--     watching a video, then export those settings into a
--     JSON file that can be used as a reference for the
--     notebook's subtitle configuration.
--
-- Supported Colab Subtitle Settings:
--     • Font Size | Font Color
--     • Outline Size | Shadow Size
--     • Position (Top / Bottom) | Vertical Margin (MarginV)
--     • Horizontal Margin (MarginL / MarginR)
--
-- Additional MPV Preview Controls:
--     • sub-pos top preset | sub-pos bottom preset
--     • sub-pos fine adjustment
--
-- Features:
--     • Real-time subtitle preview
--     • Interactive ASS overlay menu with three-pane layout
--     • Live value editing with instant preview
--     • Inactivity auto-close (15 seconds default)
--     • Startup hotkey cheat sheet
--     • User-configurable script options
--     • JSON export to current video's directory
--     • MPV subtitle property synchronization
--     • Google Colab compatible settings export
--     • Standalone hotkey shortcuts remain functional
--
-- Export Format:
--     {
--       "font_size":24,
--       "font_color":"white",
--       "outline_size":1,
--       "shadow_size":1,
--       "position":"bottom",
--       "margin_v":45,
--       "margin_lr":20
--     }
--
-- Companion Files:
--     %appdata%/mpv/scripts/collab_notebook_sub.lua
--     %appdata%/mpv/script-opts/collab_notebook_sub.conf
--
-- Notes:
--     • Intended for use with subtitle formats that MPV
--       can restyle (SRT, ASS/SSA with override enabled,
--       WebVTT, etc.).
--
--     • For best results: sub-ass-override=force
--       should be enabled in mpv.conf.
--     • Bitmap-based subtitles (PGS, VobSub, DVB, etc.)
--       cannot be fully restyled by MPV and may not reflect
--       all editor changes.
--------------------------------------------------
-- KEYBINDS
--------------------------------------------------
-- Shift+g         = Increase font size (+2)
-- Shift+f         = Decrease font size (-2)
-- Ctrl+c          = Cycle font color white -> yellow -> cyan -> black -> green
-- Ctrl+]          = Increase outline size (+1)
-- Ctrl+[          = Decrease outline size (-1)
-- Ctrl+Shift+]    = Increase shadow size (+1)
-- Ctrl+Shift+[    = Decrease shadow size (-1)
-- Ctrl+p          = Toggle subtitle position bottom <-> top
-- Alt+UP          = Increase vertical margin (+5)
-- Alt+DOWN        = Decrease vertical margin (-5)
-- Alt+RIGHT       = Increase horizontal margin (+10)
-- Alt+LEFT        = Decrease horizontal margin (-10)
-- Ctrl+t          = Set MPV sub-pos to top preset (5%)
-- Ctrl+b          = Set MPV sub-pos to bottom preset (95%)
-- Alt+r           = Increase MPV sub-pos (+1)
-- Alt+t           = Decrease MPV sub-pos (-1)
-- Ctrl+i          = Toggle interactive menu
-- Ctrl+Shift+h    = Show hotkey cheat sheet
-- Ctrl+Shift+s    = Export current Colab subtitle
--                   settings to JSON file in the
--                   currently playing video's
--                   directory
--
-- Menu Navigation (when menu is visible):
-- UP / DOWN       = Navigate categories or change values
-- LEFT            = Go back from value editing
-- RIGHT           = Enter value editing mode
-- ENTER           = Confirm selection or execute action
-- ESC             = Close menu
--------------------------------------------------

local mp = require("mp")
local options = require("mp.options")

local opts = {
    show_hotkey_cheatsheet = true,
    cheatsheet_duration = 3,
    menu_inactivity_timeout = 15
}

options.read_options(opts, "collab_notebook_sub")

-- Forward declaration required: export_json is defined later but called
-- from menu_enter(), which is defined first.
local export_json



--------------------------------------------------
-- STARTUP HOTKEY CHEATSHEET
--------------------------------------------------

local function show_hotkey_cheatsheet()

    if not opts.show_hotkey_cheatsheet then
        return
    end

    local txt =
        "Google Colab Subtitle Editor\n" ..
        "\n" ..
        "Shift+G / Shift+F   Font Size +/-\n" ..
        "Ctrl+C              Next Font Color\n" ..
        "Ctrl+] / Ctrl+[     Outline +/-\n" ..
        "Ctrl+Shift+] / [    Shadow +/-\n" ..
        "Ctrl+P              Toggle Top/Bottom\n" ..
        "Alt+UP / DOWN       Margin V +/-\n" ..
        "Alt+LEFT / RIGHT    Margin LR +/-\n" ..
        "Alt+R / Alt+T       sub-pos +/-1\n" ..
        "Ctrl+T / Ctrl+B     sub-pos Top/Bottom\n" ..
        "Ctrl+I              Toggle Menu\n" ..
        "Ctrl+Shift+S        Export JSON"

    mp.osd_message(txt, opts.cheatsheet_duration)
end

--------------------------------------------------
-- COLAB STYLE STATE
--------------------------------------------------

local state = {
    font_size = 24,
    font_color = "white",
    outline_size = 3,   -- matches mpv.conf sub-border-size=3
    shadow_size = 2,    -- matches mpv.conf sub-shadow-offset=2
    position = "bottom",
    margin_v = 45,
    margin_lr = 45,     -- matches mpv.conf sub-margin-x=45

    -- extra MPV-only preview controls
    sub_pos = 100       -- 100 = MPV's natural bottom anchor; margin_v (sub-margin-y) is then pixels from that edge
}

--------------------------------------------------
-- MENU STATE
--------------------------------------------------

local menu = {
    visible = false,
    mode = "category",  -- "category", "edit", "enum"
    selected = 1,
    inactivity_timer = nil,
    export_message = nil,
    export_message_timer = nil,

    categories = {
        {key = "font_size",     label = "Font Size",         type = "numeric", min = 12, max = 72,  step = 2},
        {key = "font_color",    label = "Font Color",        type = "enum",    values = {"white", "yellow", "cyan", "black", "green"}},
        {key = "outline_size",  label = "Outline Size",      type = "numeric", min = 0,  max = 5,   step = 1},
        {key = "shadow_size",   label = "Shadow Size",       type = "numeric", min = 0,  max = 3,   step = 1},
        {key = "position",      label = "Position",          type = "enum",    values = {"bottom", "top"}},
        {key = "margin_v",      label = "Vertical Margin",   type = "numeric", min = 0,  max = 150, step = 5},
        {key = "margin_lr",     label = "Horizontal Margin", type = "numeric", min = 0,  max = 200, step = 10},
        {key = "export",        label = "Export JSON",       type = "action"},
        {key = "close",         label = "Close",             type = "action"}
    },

    enum_selected = 1,
    enum_values = {}
}

local overlay = nil

--------------------------------------------------
-- COLOR PRESETS
--------------------------------------------------

local colors = {
    "white",
    "yellow",
    "cyan",
    "black",
    "green"
}

local mpv_colors = {
    white  = "#FFFFFF",
    yellow = "#FFFF00",
    cyan   = "#00FFFF",
    black  = "#000000",
    green  = "#00FF00"
}

--------------------------------------------------
-- HELPERS
--------------------------------------------------

local function clamp(v,minv,maxv)
    if v < minv then return minv end
    if v > maxv then return maxv end
    return v
end

local function color_index()
    for i,c in ipairs(colors) do
        if c == state.font_color then
            return i
        end
    end
    return 1
end

--------------------------------------------------
-- APPLY TO MPV
--------------------------------------------------

local function apply_state()

    mp.set_property_number(
        "sub-scale",
        state.font_size / 24.0
    )

    pcall(function()
        mp.set_property(
            "sub-color",
            mpv_colors[state.font_color]
        )
    end)

    mp.set_property_number(
        "sub-border-size",
        state.outline_size
    )

    mp.set_property_number(
        "sub-shadow-offset",
        state.shadow_size
    )

    mp.set_property_number(
        "sub-margin-y",
        state.margin_v
    )

    mp.set_property_number(
        "sub-margin-x",
        state.margin_lr
    )

    mp.set_property_number(
        "sub-pos",
        state.sub_pos
    )
end

--------------------------------------------------
-- MENU RENDERING (ASS OVERLAY)
--------------------------------------------------

local function escape_ass(text)
    text = text:gsub("\\", "\\\\")
    text = text:gsub("{", "\\{")
    text = text:gsub("}", "\\}")
    return text
end

local function get_current_value(cat)
    return tostring(state[cat.key] or "")
end

local function get_right_pane_content()
    if menu.export_message then
        return menu.export_message
    end

    local cat = menu.categories[menu.selected]

    if cat.type == "action" then
        if cat.key == "export" then
            return "Export to file"
        elseif cat.key == "close" then
            return "Close menu"
        end
    end

    if menu.mode == "category" then
        local value = get_current_value(cat)
        local hint = ""

        if cat.type == "numeric" then
            hint = "Range: " .. cat.min .. "-" .. cat.max
        elseif cat.type == "enum" then
            hint = "Options: " .. table.concat(cat.values, ", ")
        end

        return "Current: " .. value .. "\n\n" .. hint
    elseif menu.mode == "edit" or menu.mode == "enum" then
        local value = get_current_value(cat)
        return "Current: " .. value .. "\n\nEditing..."
    end

    return ""
end

local function get_controls_text()
    if menu.mode == "category" then
        return "↑ ↓  Navigate    →  Edit    Enter  Activate    Esc  Close"
    elseif menu.mode == "edit" then
        return "↑ ↓  Change Value    ←  Back    Enter  Apply"
    elseif menu.mode == "enum" then
        return "↑ ↓  Select    Enter  Confirm    ←  Back"
    end
    return ""
end

local function render_menu()
    if not menu.visible then
        if overlay then
            overlay:remove()
            overlay = nil
        end
        return
    end

    local lines = {}

    -- Box background (must be first)
    table.insert(lines, "{\\pos(30,30)\\an7\\1c&H000000&\\1a&H40&\\bord0\\shad0\\p1}m 0 0 l 660 0 660 400 0 400{\\p0}")

    -- Title
    table.insert(lines, "{\\pos(40,50)\\an7\\fs26\\b1\\1c&HFFFFFF&\\1a&H00&\\bord0\\shad0}Google Colab Subtitle Editor")

    -- Top divider line
    table.insert(lines, "{\\pos(40,80)\\an7\\1c&HFFFFFF&\\1a&H80&\\bord0\\shad0\\p1}m 0 0 l 620 0{\\p0}")

    -- Left pane: categories
    local y = 100
    for i, cat in ipairs(menu.categories) do
        local prefix = (i == menu.selected) and "► " or "  "
        local color = (i == menu.selected) and "&HFFFFFF&" or "&HC0C0C0&"

        table.insert(lines, "{\\pos(50," .. y .. ")\\an7\\fs22\\1c" .. color .. "\\1a&H00&\\bord0\\shad0}" .. escape_ass(prefix .. cat.label))

        y = y + 30
    end

    -- Middle divider
    table.insert(lines, "{\\pos(340,90)\\an7\\1c&HFFFFFF&\\1a&H80&\\bord0\\shad0\\p1}m 0 0 l 0 305{\\p0}")

    -- Right pane: value/hint or enum list
    if menu.mode == "enum" then
        -- Show enum list
        local enum_y = 100
        for i, val in ipairs(menu.enum_values) do
            local enum_prefix = (i == menu.enum_selected) and "► " or "  "
            local enum_color = (i == menu.enum_selected) and "&HFFFFFF&" or "&HC0C0C0&"

            table.insert(lines, "{\\pos(360," .. enum_y .. ")\\an7\\fs22\\1c" .. enum_color .. "\\1a&H00&\\bord0\\shad0}" .. escape_ass(enum_prefix .. val))
            enum_y = enum_y + 30
        end
    else
        -- Show current value and hint
        local right_content = get_right_pane_content()
        local right_lines = {}
        for line in right_content:gmatch("([^\n]+)") do
            table.insert(right_lines, line)
        end

        local right_y = 100
        for _, line in ipairs(right_lines) do
            table.insert(lines, "{\\pos(360," .. right_y .. ")\\an7\\fs22\\1c&HFFFFFF&\\1a&H00&\\bord0\\shad0}" .. escape_ass(line))
            right_y = right_y + 30
        end
    end

    -- Bottom divider
    table.insert(lines, "{\\pos(40,365)\\an7\\1c&HFFFFFF&\\1a&H80&\\bord0\\shad0\\p1}m 0 0 l 620 0{\\p0}")

    -- Controls
    local controls = get_controls_text()
    table.insert(lines, "{\\pos(40,380)\\an7\\fs20\\1c&HAAAAAA&\\1a&H00&\\bord0\\shad0}" .. escape_ass(controls))

    -- Join all lines (each must be a separate ASS event line, not \N within one event)
    local ass = table.concat(lines, "\n")

    -- Create or update overlay
    if not overlay then
        overlay = mp.create_osd_overlay("ass-events")
    end

    overlay.data = ass
    overlay:update()
end

local function reset_inactivity_timer()
    if menu.inactivity_timer then
        menu.inactivity_timer:kill()
    end

    menu.inactivity_timer = mp.add_timeout(opts.menu_inactivity_timeout, function()
        menu.visible = false
        render_menu()
    end)
end

local function clear_export_message()
    if menu.export_message_timer then
        menu.export_message_timer:kill()
        menu.export_message_timer = nil
    end
    menu.export_message = nil
    render_menu()
end

local function show_export_message(msg)
    menu.export_message = msg

    if menu.export_message_timer then
        menu.export_message_timer:kill()
    end

    menu.export_message_timer = mp.add_timeout(3, clear_export_message)
    render_menu()
end

local function refresh()
    apply_state()
    if menu.visible then
        render_menu()
    end
end

--------------------------------------------------
-- MENU NAVIGATION
--------------------------------------------------

local function menu_up()
    if not menu.visible then return end
    reset_inactivity_timer()

    if menu.mode == "category" then
        menu.selected = menu.selected - 1
        if menu.selected < 1 then
            menu.selected = #menu.categories
        end
    elseif menu.mode == "edit" then
        local cat = menu.categories[menu.selected]
        local new_val = state[cat.key] + cat.step
        state[cat.key] = clamp(new_val, cat.min, cat.max)
        apply_state()
    elseif menu.mode == "enum" then
        menu.enum_selected = menu.enum_selected - 1
        if menu.enum_selected < 1 then
            menu.enum_selected = #menu.enum_values
        end
    end

    render_menu()
end

local function menu_down()
    if not menu.visible then return end
    reset_inactivity_timer()

    if menu.mode == "category" then
        menu.selected = menu.selected + 1
        if menu.selected > #menu.categories then
            menu.selected = 1
        end
    elseif menu.mode == "edit" then
        local cat = menu.categories[menu.selected]
        local new_val = state[cat.key] - cat.step
        state[cat.key] = clamp(new_val, cat.min, cat.max)
        apply_state()
    elseif menu.mode == "enum" then
        menu.enum_selected = menu.enum_selected + 1
        if menu.enum_selected > #menu.enum_values then
            menu.enum_selected = 1
        end
    end

    render_menu()
end

local function menu_right()
    if not menu.visible then return end
    reset_inactivity_timer()

    if menu.mode == "category" then
        if menu.selected < 1 or menu.selected > #menu.categories then
            menu.selected = 1
        end
        local cat = menu.categories[menu.selected]

        if cat.type == "numeric" then
            menu.mode = "edit"
        elseif cat.type == "enum" then
            menu.mode = "enum"
            menu.enum_values = cat.values

            -- Find current selection; default to 1 if not found
            menu.enum_selected = 1
            local current = state[cat.key]
            for i, v in ipairs(menu.enum_values) do
                if v == current then
                    menu.enum_selected = i
                    break
                end
            end
        end
    end

    render_menu()
end

local function menu_left()
    if not menu.visible then return end
    reset_inactivity_timer()

    if menu.mode == "edit" or menu.mode == "enum" then
        menu.mode = "category"
    end

    render_menu()
end

local function menu_enter()
    if not menu.visible then return end
    reset_inactivity_timer()

    if menu.selected < 1 or menu.selected > #menu.categories then
        menu.selected = 1
        render_menu()
        return
    end

    local cat = menu.categories[menu.selected]

    if menu.mode == "category" then
        if cat.type == "action" then
            if cat.key == "export" then
                export_json()
            elseif cat.key == "close" then
                menu.visible = false
                render_menu()
            end
        else
            menu_right()
        end
    elseif menu.mode == "edit" then
        menu.mode = "category"
    elseif menu.mode == "enum" then
        local selected_value = menu.enum_values[menu.enum_selected]
        state[cat.key] = selected_value
        -- Sync sub_pos when position changes so subtitle actually moves
        if cat.key == "position" then
            state.sub_pos = (selected_value == "top") and 5 or 100
        end
        apply_state()
        menu.mode = "category"
    end

    render_menu()
end

local function menu_escape()
    if not menu.visible then return end

    menu.visible = false
    if menu.export_message_timer then
        menu.export_message_timer:kill()
        menu.export_message_timer = nil
    end
    menu.export_message = nil
    render_menu()
end

local function toggle_menu()
    menu.visible = not menu.visible

    if menu.visible then
        menu.mode = "category"
        menu.selected = 1
        reset_inactivity_timer()
    else
        if menu.inactivity_timer then
            menu.inactivity_timer:kill()
        end
        if menu.export_message_timer then
            menu.export_message_timer:kill()
            menu.export_message_timer = nil
        end
        menu.export_message = nil
    end

    render_menu()
end

--------------------------------------------------
-- FONT SIZE
--------------------------------------------------

local function font_size_up()
    state.font_size =
        clamp(state.font_size + 2, 12, 72)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

local function font_size_down()
    state.font_size =
        clamp(state.font_size - 2, 12, 72)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- FONT COLOR
--------------------------------------------------

local function next_color()
    local idx = color_index()
    idx = idx + 1

    if idx > #colors then
        idx = 1
    end

    state.font_color = colors[idx]
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- OUTLINE
--------------------------------------------------

local function outline_up()
    state.outline_size =
        clamp(state.outline_size + 1, 0, 5)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

local function outline_down()
    state.outline_size =
        clamp(state.outline_size - 1, 0, 5)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- SHADOW
--------------------------------------------------

local function shadow_up()
    state.shadow_size =
        clamp(state.shadow_size + 1, 0, 3)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

local function shadow_down()
    state.shadow_size =
        clamp(state.shadow_size - 1, 0, 3)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- TOP/BOTTOM TOGGLE
--------------------------------------------------

local function toggle_position()
    if state.position == "bottom" then
        state.position = "top"
        state.sub_pos = 5
    else
        state.position = "bottom"
        state.sub_pos = 100
    end
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- VERTICAL MARGIN
--------------------------------------------------

local function margin_v_up()
    state.margin_v =
        clamp(state.margin_v + 5, 0, 150)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

local function margin_v_down()
    state.margin_v =
        clamp(state.margin_v - 5, 0, 150)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- HORIZONTAL MARGIN
--------------------------------------------------

local function margin_lr_up()
    state.margin_lr =
        clamp(state.margin_lr + 10, 0, 200)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

local function margin_lr_down()
    state.margin_lr =
        clamp(state.margin_lr - 10, 0, 200)
    refresh()
    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- SUB POS
--------------------------------------------------

local function sub_pos_up()
    state.sub_pos =
        clamp(state.sub_pos + 1, 0, 150)

    mp.set_property_number(
        "sub-pos",
        state.sub_pos
    )

    if menu.visible then reset_inactivity_timer() end
end

local function sub_pos_down()
    state.sub_pos =
        clamp(state.sub_pos - 1, 0, 150)

    mp.set_property_number(
        "sub-pos",
        state.sub_pos
    )

    if menu.visible then reset_inactivity_timer() end
end

local function sub_pos_top()
    state.sub_pos = 5

    mp.set_property_number(
        "sub-pos",
        state.sub_pos
    )

    if menu.visible then reset_inactivity_timer() end
end

local function sub_pos_bottom()
    state.sub_pos = 100

    mp.set_property_number(
        "sub-pos",
        state.sub_pos
    )

    if menu.visible then reset_inactivity_timer() end
end

--------------------------------------------------
-- EXPORT JSON
--------------------------------------------------

local function dirname(path)
    -- Handle both / and \ separators on all platforms
    local dir = path:match("^(.*[/\\])")
    if not dir then
        return "." .. package.config:sub(1,1)
    end
    return dir
end

local function basename_no_ext(path)

    local name =
        path:match("([^/\\]+)$")

    if not name then
        return "video"
    end

    return (name:gsub("%.[^.]+$", ""))
end

export_json = function()

    local path = mp.get_property("path")

    if not path then
        if menu.visible then
            show_export_message("✗ No file loaded")
        else
            mp.osd_message(
                "No file loaded",
                3
            )
        end
        return
    end

    local dir  = dirname(path)
    local stem = basename_no_ext(path)

    local outfile =
        dir ..
        stem ..
        ".subtitle-style.json"

    local json =
        "{\n" ..
        '  "font_size":' .. state.font_size .. ",\n" ..
        '  "font_color":"' .. state.font_color .. '",\n' ..
        '  "outline_size":' .. state.outline_size .. ",\n" ..
        '  "shadow_size":' .. state.shadow_size .. ",\n" ..
        '  "position":"' .. state.position .. '",\n' ..
        '  "margin_v":' .. state.margin_v .. ",\n" ..
        '  "margin_lr":' .. state.margin_lr .. "\n" ..
        "}\n"

    local f,err = io.open(outfile,"w")

    if not f then
        if menu.visible then
            show_export_message("✗ Export failed:\n" .. tostring(err))
        else
            mp.osd_message(
                "Export failed:\n" .. tostring(err),
                5
            )
        end
        return
    end

    f:write(json)
    f:close()

    if menu.visible then
        local filename = outfile:match("([^/\\]+)$") or outfile
        show_export_message("✓ Exported:\n" .. filename)
    else
        mp.osd_message(
            "Exported:\n" .. outfile,
            5
        )
    end
end

--------------------------------------------------
-- KEYBINDS
--------------------------------------------------

-- font size
mp.add_key_binding(
    "Shift+g",
    "font_size_up",
    font_size_up
)

mp.add_key_binding(
    "Shift+f",
    "font_size_down",
    font_size_down
)

-- color
mp.add_key_binding(
    "Ctrl+c",
    "next_color",
    next_color
)

-- outline
mp.add_key_binding(
    "Ctrl+]",
    "outline_up",
    outline_up
)

mp.add_key_binding(
    "Ctrl+[",
    "outline_down",
    outline_down
)

-- shadow
mp.add_key_binding(
    "Ctrl+Shift+]",
    "shadow_up",
    shadow_up
)

mp.add_key_binding(
    "Ctrl+Shift+[",
    "shadow_down",
    shadow_down
)

-- top/bottom toggle
mp.add_key_binding(
    "Ctrl+p",
    "toggle_position",
    toggle_position
)

-- notebook vertical margin
mp.add_key_binding(
    "Alt+UP",
    "margin_v_up",
    margin_v_up
)

mp.add_key_binding(
    "Alt+DOWN",
    "margin_v_down",
    margin_v_down
)

-- notebook horizontal margin
mp.add_key_binding(
    "Alt+RIGHT",
    "margin_lr_up",
    margin_lr_up
)

mp.add_key_binding(
    "Alt+LEFT",
    "margin_lr_down",
    margin_lr_down
)

-- MPV sub-pos presets
mp.add_key_binding(
    "Ctrl+t",
    "sub_pos_top",
    sub_pos_top
)

mp.add_key_binding(
    "Ctrl+b",
    "sub_pos_bottom",
    sub_pos_bottom
)

-- MPV sub-pos incremental
mp.add_key_binding(
    "Alt+r",
    "sub_pos_up",
    sub_pos_up
)

mp.add_key_binding(
    "Alt+t",
    "sub_pos_down",
    sub_pos_down
)

-- export
mp.add_key_binding(
    "Ctrl+Shift+s",
    "export_colab_json",
    export_json
)

-- menu toggle
mp.add_key_binding(
    "Ctrl+i",
    "toggle_menu",
    toggle_menu
)

mp.add_key_binding(
    "Ctrl+Shift+h",
    "show_colab_help",
    show_hotkey_cheatsheet
)

-- menu navigation
-- mp.add_forced_key_binding is required here: input.conf bindings (e.g.
-- ENTER playlist-next) take precedence over mp.add_key_binding, which
-- would prevent the menu from receiving these keys at all.
-- When menu.visible is false each handler returns immediately, so the
-- key falls through to normal MPV/input.conf behaviour (official docs:
-- "when handler returns without performing actions, key behaviour follows
-- normal binding precedence").
mp.add_forced_key_binding(
    "UP",
    "menu_up",
    menu_up
)

mp.add_forced_key_binding(
    "DOWN",
    "menu_down",
    menu_down
)

mp.add_forced_key_binding(
    "LEFT",
    "menu_left",
    menu_left
)

mp.add_forced_key_binding(
    "RIGHT",
    "menu_right",
    menu_right
)

mp.add_forced_key_binding(
    "ENTER",
    "menu_enter",
    menu_enter
)

mp.add_forced_key_binding(
    "ESC",
    "menu_escape",
    menu_escape
)



--------------------------------------------------
-- INIT
--------------------------------------------------

mp.register_event(
    "file-loaded",
    function()

        -- Reset menu state on new file load
        if menu.inactivity_timer then
            menu.inactivity_timer:kill()
            menu.inactivity_timer = nil
        end
        if menu.export_message_timer then
            menu.export_message_timer:kill()
            menu.export_message_timer = nil
        end
        menu.export_message = nil
        menu.visible = false
        menu.mode = "category"
        menu.selected = 1

        apply_state()

        show_hotkey_cheatsheet()

    end
)