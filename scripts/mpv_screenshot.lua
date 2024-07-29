
function screenshot_directory_hook(event)
    if event == "file-loaded" then
        local filepath = mp.get_property("path")
        if filepath ~= nil then
            local dir = mp.utils.split_path(filepath)
            mp.set_property("screenshot-directory", dir)
        end
    end
end

mp.register_event("file-loaded", screenshot_directory_hook)
