<?php

final class Database
{
    private static ?PDO $pdo = null;

    public static function connection(): PDO
    {
        if (self::$pdo === null) {
            $host = getenv('POSTGRES_HOST') ?: 'db';
            $port = getenv('POSTGRES_PORT') ?: '5432';
            $db = getenv('POSTGRES_DB') ?: 'anuario_pa';
            $user = getenv('POSTGRES_USER') ?: 'anuario';
            $pass = getenv('POSTGRES_PASSWORD') ?: 'anuario';

            $dsn = "pgsql:host={$host};port={$port};dbname={$db}";
            self::$pdo = new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
        }
        return self::$pdo;
    }
}
