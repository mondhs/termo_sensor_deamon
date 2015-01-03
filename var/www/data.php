<?php
header("Content-Type: text/plain");
$page=$_GET['page'];
$page = $page == null? 0:$page;
$myfile = fopen("/var/local/mg_termo_service/data_archive.csv".$page, "r") or die("Unable to open file!");
echo fread($myfile,filesize("/var/local/mg_termo_service/data_archive.csv".$page)) . "\n";
fclose($myfile);
?>

