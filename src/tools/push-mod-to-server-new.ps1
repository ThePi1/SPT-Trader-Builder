# Copy mod files from dev folder to server
$local_data_path = "I:\Games\rtt2-beta-4-0-13\Development\rtt2-traders2"
$server_data_path = "\\192.168.1.42\Share\rtt2-4-0-13-clean\SPT\user\mods\rtt2"
Remove-Item ($server_data_path + "\*") -Recurse

# Copy latest mod dll from output folder to server
$local_mod_path = "I:\Games\rtt2-beta-4-0-13\SPT\user\mods\rtt2"
$server_mod_path = "\\192.168.1.42\Share\rtt2-4-0-13-clean\SPT\user\mods\rtt2"
Robocopy.exe  $local_mod_path $server_mod_path "rtt2traders.dll" /mt /z

Robocopy.exe $local_data_path"\data" $server_data_path"\data" /mt /z /e
Robocopy.exe $local_data_path"\db" $server_data_path"\db" /mt /z /e
Robocopy.exe $local_data_path"\bundles" $server_data_path"\bundles" /mt /z /e
Robocopy.exe $local_data_path $server_data_path bundles.json /mt /z /e