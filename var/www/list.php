<?php
header('Content-Type: application/json');
$files = glob('/var/local/mg_termo_service/data_archive.csv*');
$regex = '/\d+$/';
$pages = array(); 
foreach($files as $file){
    //$pages[] = $file;
    if(preg_match($regex, $file, $match)){
        //echo $match[0];
        $pages[] = $match[0];
    }
}
echo json_encode($pages);
?>


