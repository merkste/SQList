{ stdenv, sqlistSrc ? { outPath = ./.; }, python }:

python.pkgs.buildPythonApplication {
  pname = "sqlist";
  version = "0.1";
  src = sqlistSrc;
  doCheck = false;
  buildPhase = "";
  installPhase = ''
    mkdir -p $out/bin $out/share
    cp -p *.py $out/share
    chmod +x $out/share/sqlist.py
    ln -s $out/share/sqlist.py $out/bin/sqlist
  '';

  meta = with stdenv.lib; {
    description = "Use SQL-like queries to work on a CSV file";
    homepage = https://gitlab.tcs.inf.tu-dresden.de/maercker/sqlist;
    license = licenses.gpl2;
    maintainers = [ maintainers.spacefrogg ];
  };
}
