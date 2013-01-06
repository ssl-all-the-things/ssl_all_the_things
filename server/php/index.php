<?php

$link = mysql_connect('localhost', 'root', 'fdmtfw12');
if (!$link) {
        die('Could not connect: ' . mysql_error());
}
mysql_select_db('ssl_all_the_things') or die('Could not select database');


/*
 * 'N' - Not assigned
 * 'F' - Finished
 * 'I' = In progress
 */
function get_assignment() {
    mysql_query("LOCK TABLES ipv4_dispatch READ");
    mysql_query("LOCK TABLES ipv4_dispatch WRITE");

    $query = 'SELECT oct_a, oct_b FROM ipv4_dispatch WHERE status = \'N\' LIMIT 1';
    $result = mysql_query($query) or die('Query failed: ' . mysql_error());

    /* Get top line */
    $line = mysql_fetch_array($result, MYSQL_ASSOC);

    $a = $line["oct_a"];
    $b = $line["oct_b"]; 

    /* Finish */
    mysql_free_result($result);

    $query = "UPDATE ipv4_dispatch set status = 'I' where oct_a = $a and oct_b = $b";
    mysql_query($query) or die('Query failed: ' . mysql_error());

    mysql_query("UNLOCK TABLES");

    echo "{\n";
    echo "    \"ipv\": 4,\n";
    echo "    \"oct_a\": $a,\n";
    echo "    \"oct_b\": $b,\n";
    echo "    \"oct_c\": 0,\n";
    echo "    \"oct_d\": 0,\n";
    echo "    \"slash\": 16\n";
    echo "}\n";

    return $line;
}


$assignment = get_assignment();


mysql_close($link);



?>
