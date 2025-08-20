import subprocess
import textwrap

import pytest
import os

@pytest.fixture
def setup_files(tmp_path):
    # Create temporary XML and XSLT files
    xml_file = tmp_path / "input.xml"
    xslt_file = "../conversion-script.xslt"
    output_file = tmp_path / "output.txt"

    xml_file.write_text(textwrap.dedent(
        """
            <TEI xmlns="http://www.tei-c.org/ns/1.0">
              <teiHeader>
                <fileDesc>
                  <sourceDesc>
                    <msDesc>
                      <msIdentifier xml:id="W123"/>
                    </msDesc>
                  </sourceDesc>
                </fileDesc>
              </teiHeader>
              <text>
                <body>
                  <div>
                    <p>
                      <lb/><hi rend="underline">underlined with space after</hi> and more text. 
                      <lb/>A <hi rend="rubricated">L</hi>etter.
                      <lb/>An inword<add>addi</add>tion.
                      <lb/>A <del rend="strikethrough">deleted</del> word. Fur
                      <lb break="no"/>thermore an in word break.
                    </p>
                  </div>
                </body>
              </text>
            </TEI>
        """),
                        encoding="utf-8")

    return str(xml_file), str(xslt_file), str(output_file)

def test_saxon_transformation(setup_files):
    xml_file, xslt_file, output_file = setup_files

    # Path to Saxon-HE JAR
    saxon_jar = "../vendor/saxon9he.jar"

    # Run Saxon transformation
    result = subprocess.run([
        "java", "-jar", saxon_jar,
        "-s:" + xml_file,
        "-xsl:" + xslt_file,
        "-o:" + output_file
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Saxon failed: {result.stderr}"

    output = open(output_file, encoding="utf-8").read().strip()
    output_content = output.split("content:\n")[1][:-1].strip()

    expected = "{underline=underlined with space after} and more text. A Letter. An inword{add=addi-}tion. A {del=deleted-strikethrough} word. Furthermore an in word break."  # your expected output

    assert output_content == expected

