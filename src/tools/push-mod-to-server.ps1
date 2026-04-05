# Copy latest mod dll from output folder to server
$local_mod_path = "I:\Games\rtt2-beta\BepInEx\plugins"
$server_mod_path = "\\192.168.1.42\Share\rtt2-beta\SPT\user\mods\rtt2-traders"
Remove-Item ($server_mod_path + "\rtt2traders.dll")
Robocopy.exe  $local_mod_path $server_mod_path "rtt2traders.dll" /mt /z
# Copy mod files from dev folder to server
$local_data_path = "I:\Games\rtt2-beta\Development\rtt2-traders2"
$server_data_path = "\\192.168.1.42\Share\rtt2-beta\SPT\user\mods\rtt2-traders"
Remove-Item ($server_data_path + "\data") -Recurse
Remove-Item ($server_data_path + "\db") -Recurse
Robocopy.exe $local_data_path"\data" $server_data_path"\data" /mt /z /e
Robocopy.exe $local_data_path"\db" $server_data_path"\db" /mt /z /e

